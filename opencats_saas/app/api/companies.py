"""
Companies API Endpoints
"""
from flask import request, jsonify
from app.api import api_bp
from app.api.auth import token_required
from app.api.schemas import company_schema, companies_schema, contact_schema, joborder_schema
from app.models import Company, Contact, JobOrder, Activity
from app.extensions import db
from sqlalchemy import or_
from marshmallow import ValidationError


@api_bp.route('/companies', methods=['GET'])
@token_required
def get_companies(current_user):
    """
    List companies with filtering and pagination

    GET /api/v1/companies?page=1&per_page=20&search=tech&hot_only=true
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    query = Company.query_for_site(current_user.site_id).filter_by(is_admin_hidden=False)

    # Search
    search = request.args.get('search')
    if search:
        search_filter = or_(
            Company.name.ilike(f'%{search}%'),
            Company.city.ilike(f'%{search}%'),
            Company.key_technologies.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)

    # Hot companies only
    if request.args.get('hot_only') == 'true':
        query = query.filter_by(is_hot=True)

    # Location filters
    city = request.args.get('city')
    if city:
        query = query.filter_by(city=city)

    state = request.args.get('state')
    if state:
        query = query.filter_by(state=state)

    # Sort
    sort_by = request.args.get('sort', 'name')
    sort_order = request.args.get('order', 'asc')

    if hasattr(Company, sort_by):
        sort_column = getattr(Company, sort_by)
        if sort_order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'data': companies_schema.dump(pagination.items),
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200


@api_bp.route('/companies/<int:id>', methods=['GET'])
@token_required
def get_company(current_user, id):
    """
    Get single company by ID

    GET /api/v1/companies/123

    Returns company with contacts and job orders
    """
    company = Company.query_for_site(current_user.site_id).filter_by(company_id=id).first_or_404()

    if company.is_admin_hidden:
        return jsonify({'error': 'Company not found'}), 404

    data = company_schema.dump(company)

    # Add contacts
    contacts = Contact.query_for_site(current_user.site_id).filter_by(
        company_id=id
    ).all()
    data['contacts'] = [
        {
            'contact_id': c.contact_id,
            'first_name': c.first_name,
            'last_name': c.last_name,
            'title': c.title,
            'email1': c.email1,
            'phone_work': c.phone_work,
            'is_hot': c.is_hot
        }
        for c in contacts
    ]

    # Add job orders
    jobs = JobOrder.query_for_site(current_user.site_id).filter_by(
        company_id=id,
        is_admin_hidden=False
    ).order_by(JobOrder.date_created.desc()).limit(10).all()
    data['job_orders'] = [
        {
            'joborder_id': j.joborder_id,
            'title': j.title,
            'status': j.status,
            'openings': j.openings,
            'openings_available': j.openings_available,
            'date_created': j.date_created.isoformat() if j.date_created else None
        }
        for j in jobs
    ]

    return jsonify(data), 200


@api_bp.route('/companies', methods=['POST'])
@token_required
def create_company(current_user):
    """
    Create new company

    POST /api/v1/companies
    {
        "name": "TechCorp Inc",
        "phone1": "555-1234",
        "url": "https://techcorp.com",
        "city": "San Francisco",
        "state": "CA"
    }
    """
    try:
        data = company_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400

    # Check duplicates
    existing = Company.query_for_site(current_user.site_id).filter_by(
        name=data['name'],
        is_admin_hidden=False
    ).first()
    if existing:
        return jsonify({
            'error': 'Duplicate company',
            'message': 'Company with this name already exists',
            'existing_id': existing.company_id
        }), 409

    # Create company
    company = Company(site_id=current_user.site_id, **data)
    company.owner = current_user.user_id
    company.entered_by = current_user.user_id

    db.session.add(company)
    db.session.commit()

    # Log activity
    activity = Activity(
        site_id=current_user.site_id,
        data_item_id=company.company_id,
        data_item_type=300,  # Company
        type=300,  # Created
        entered_by=current_user.user_id,
        notes=f'Company created via API'
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify(company_schema.dump(company)), 201


@api_bp.route('/companies/<int:id>', methods=['PUT'])
@token_required
def update_company(current_user, id):
    """
    Update company

    PUT /api/v1/companies/123
    {
        "phone1": "555-5678",
        "notes": "Updated contact information"
    }
    """
    company = Company.query_for_site(current_user.site_id).filter_by(company_id=id).first_or_404()

    if company.is_admin_hidden:
        return jsonify({'error': 'Company not found'}), 404

    try:
        data = company_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400

    # Update fields
    for key, value in data.items():
        if hasattr(company, key):
            setattr(company, key, value)

    company.date_modified_by = current_user.user_id

    db.session.commit()

    # Log activity
    activity = Activity(
        site_id=current_user.site_id,
        data_item_id=company.company_id,
        data_item_type=300,
        type=500,  # Modified
        entered_by=current_user.user_id,
        notes=f'Company updated via API'
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify(company_schema.dump(company)), 200


@api_bp.route('/companies/<int:id>', methods=['DELETE'])
@token_required
def delete_company(current_user, id):
    """
    Delete company (soft delete)

    DELETE /api/v1/companies/123
    """
    company = Company.query_for_site(current_user.site_id).filter_by(company_id=id).first_or_404()

    if company.is_admin_hidden:
        return jsonify({'error': 'Company not found'}), 404

    # Check for dependencies
    active_jobs = JobOrder.query_for_site(current_user.site_id).filter_by(
        company_id=id,
        is_admin_hidden=False
    ).filter(JobOrder.status.in_([0, 1])).count()

    if active_jobs > 0:
        return jsonify({
            'error': 'Cannot delete',
            'message': f'Company has {active_jobs} active job orders'
        }), 409

    # Soft delete
    company.is_admin_hidden = True
    company.date_modified_by = current_user.user_id

    db.session.commit()

    # Log activity
    activity = Activity(
        site_id=current_user.site_id,
        data_item_id=company.company_id,
        data_item_type=300,
        type=600,  # Deleted
        entered_by=current_user.user_id,
        notes=f'Company deleted via API'
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify({'message': 'Company deleted successfully'}), 200
