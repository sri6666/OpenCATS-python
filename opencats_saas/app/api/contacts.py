"""
Contacts API Endpoints
"""
from flask import request, jsonify
from app.api import api_bp
from app.api.auth import token_required
from app.api.schemas import contact_schema, contacts_schema
from app.models import Contact, Company, Activity
from app.extensions import db
from sqlalchemy import or_
from marshmallow import ValidationError


@api_bp.route('/contacts', methods=['GET'])
@token_required
def get_contacts(current_user):
    """
    List contacts with filtering and pagination

    GET /api/v1/contacts?page=1&per_page=20&company_id=10&hot_only=true
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    query = Contact.query_for_site(current_user.site_id).filter_by(is_admin_hidden=False)

    # Company filter
    company_id = request.args.get('company_id', type=int)
    if company_id:
        query = query.filter_by(company_id=company_id)

    # Search
    search = request.args.get('search')
    if search:
        search_filter = or_(
            Contact.first_name.ilike(f'%{search}%'),
            Contact.last_name.ilike(f'%{search}%'),
            Contact.email1.ilike(f'%{search}%'),
            Contact.title.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)

    # Hot contacts only
    if request.args.get('hot_only') == 'true':
        query = query.filter_by(is_hot=True)

    # Active only (not left company)
    if request.args.get('active_only') == 'true':
        query = query.filter_by(left_company=False)

    # Sort
    sort_by = request.args.get('sort', 'last_name')
    sort_order = request.args.get('order', 'asc')

    if hasattr(Contact, sort_by):
        sort_column = getattr(Contact, sort_by)
        if sort_order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Enhance with company names
    items = []
    for contact in pagination.items:
        data = contact_schema.dump(contact)
        if contact.company:
            data['company_name'] = contact.company.name
        items.append(data)

    return jsonify({
        'data': items,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200


@api_bp.route('/contacts/<int:id>', methods=['GET'])
@token_required
def get_contact(current_user, id):
    """
    Get single contact by ID

    GET /api/v1/contacts/123
    """
    contact = Contact.query_for_site(current_user.site_id).get_or_404(id)

    if contact.is_admin_hidden:
        return jsonify({'error': 'Contact not found'}), 404

    data = contact_schema.dump(contact)

    # Add company info
    if contact.company:
        data['company_name'] = contact.company.name
        data['company'] = {
            'company_id': contact.company.company_id,
            'name': contact.company.name,
            'phone1': contact.company.phone1,
            'city': contact.company.city,
            'state': contact.company.state
        }

    # Add reporting hierarchy
    if contact.reports_to:
        manager = Contact.query_for_site(current_user.site_id).get(contact.reports_to)
        if manager:
            data['manager'] = {
                'contact_id': manager.contact_id,
                'first_name': manager.first_name,
                'last_name': manager.last_name,
                'title': manager.title
            }

    return jsonify(data), 200


@api_bp.route('/contacts', methods=['POST'])
@token_required
def create_contact(current_user):
    """
    Create new contact

    POST /api/v1/contacts
    {
        "company_id": 10,
        "first_name": "Jane",
        "last_name": "Smith",
        "title": "Hiring Manager",
        "email1": "jane@techcorp.com",
        "phone_work": "555-1234"
    }
    """
    try:
        data = contact_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400

    # Verify company exists
    company = Company.query_for_site(current_user.site_id).get(data['company_id'])
    if not company or company.is_admin_hidden:
        return jsonify({'error': 'Company not found'}), 404

    # Check duplicates
    if data.get('email1'):
        existing = Contact.query_for_site(current_user.site_id).filter_by(
            email1=data['email1'],
            company_id=data['company_id'],
            is_admin_hidden=False
        ).first()
        if existing:
            return jsonify({
                'error': 'Duplicate contact',
                'message': 'Contact with this email already exists at this company',
                'existing_id': existing.contact_id
            }), 409

    # Create contact
    contact = Contact(site_id=current_user.site_id, **data)
    contact.owner = current_user.user_id
    contact.entered_by = current_user.user_id

    db.session.add(contact)
    db.session.commit()

    # Log activity
    activity = Activity(
        site_id=current_user.site_id,
        data_item_id=contact.contact_id,
        data_item_type=400,  # Contact
        type=300,  # Created
        entered_by=current_user.user_id,
        notes=f'Contact created via API'
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify(contact_schema.dump(contact)), 201


@api_bp.route('/contacts/<int:id>', methods=['PUT'])
@token_required
def update_contact(current_user, id):
    """
    Update contact

    PUT /api/v1/contacts/123
    {
        "title": "Senior Hiring Manager",
        "phone_work": "555-5678"
    }
    """
    contact = Contact.query_for_site(current_user.site_id).get_or_404(id)

    if contact.is_admin_hidden:
        return jsonify({'error': 'Contact not found'}), 404

    try:
        data = contact_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400

    # Update fields
    for key, value in data.items():
        if hasattr(contact, key):
            setattr(contact, key, value)

    contact.date_modified_by = current_user.user_id

    db.session.commit()

    # Log activity
    activity = Activity(
        site_id=current_user.site_id,
        data_item_id=contact.contact_id,
        data_item_type=400,
        type=500,  # Modified
        entered_by=current_user.user_id,
        notes=f'Contact updated via API'
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify(contact_schema.dump(contact)), 200


@api_bp.route('/contacts/<int:id>', methods=['DELETE'])
@token_required
def delete_contact(current_user, id):
    """
    Delete contact (soft delete)

    DELETE /api/v1/contacts/123
    """
    contact = Contact.query_for_site(current_user.site_id).get_or_404(id)

    if contact.is_admin_hidden:
        return jsonify({'error': 'Contact not found'}), 404

    # Soft delete
    contact.is_admin_hidden = True
    contact.date_modified_by = current_user.user_id

    db.session.commit()

    # Log activity
    activity = Activity(
        site_id=current_user.site_id,
        data_item_id=contact.contact_id,
        data_item_type=400,
        type=600,  # Deleted
        entered_by=current_user.user_id,
        notes=f'Contact deleted via API'
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify({'message': 'Contact deleted successfully'}), 200


@api_bp.route('/contacts/<int:id>/mark-left-company', methods=['POST'])
@token_required
def mark_left_company(current_user, id):
    """
    Mark contact as having left the company

    POST /api/v1/contacts/123/mark-left-company
    """
    contact = Contact.query_for_site(current_user.site_id).get_or_404(id)

    if contact.is_admin_hidden:
        return jsonify({'error': 'Contact not found'}), 404

    contact.left_company = True
    contact.date_modified_by = current_user.user_id

    db.session.commit()

    # Log activity
    activity = Activity(
        site_id=current_user.site_id,
        data_item_id=contact.contact_id,
        data_item_type=400,
        type=500,
        entered_by=current_user.user_id,
        notes=f'Contact marked as left company'
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify(contact_schema.dump(contact)), 200
