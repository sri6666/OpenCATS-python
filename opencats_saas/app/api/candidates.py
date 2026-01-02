"""
Candidates API Endpoints
"""
from flask import request, jsonify
from app.api import api_bp
from app.api.auth import token_required
from app.api.schemas import (
    candidate_schema, candidates_schema,
    pipeline_entry_schema, pipeline_entries_schema
)
from app.models import Candidate, CandidateJobOrder, Attachment, Activity
from app.extensions import db
from sqlalchemy import or_
from marshmallow import ValidationError


@api_bp.route('/candidates', methods=['GET'])
@token_required
def get_candidates(current_user):
    """
    List candidates with filtering and pagination

    GET /api/v1/candidates?page=1&per_page=20&search=python&hot_only=true

    Returns:
    {
        "data": [...],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total": 150,
            "pages": 8,
            "has_next": true,
            "has_prev": false
        }
    }
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    query = Candidate.query_for_site(current_user.site_id).filter_by(is_admin_hidden=False)

    # Search
    search = request.args.get('search')
    if search:
        search_filter = or_(
            Candidate.first_name.ilike(f'%{search}%'),
            Candidate.last_name.ilike(f'%{search}%'),
            Candidate.email1.ilike(f'%{search}%'),
            Candidate.key_skills.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)

    # Hot candidates only
    if request.args.get('hot_only') == 'true':
        query = query.filter_by(is_hot=True)

    # Active only
    if request.args.get('active_only') == 'true':
        query = query.filter_by(is_active=True)

    # Sort
    sort_by = request.args.get('sort', 'date_created')
    sort_order = request.args.get('order', 'desc')

    if hasattr(Candidate, sort_by):
        sort_column = getattr(Candidate, sort_by)
        if sort_order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'data': candidates_schema.dump(pagination.items),
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200


@api_bp.route('/candidates/<int:id>', methods=['GET'])
@token_required
def get_candidate(current_user, id):
    """
    Get single candidate by ID

    GET /api/v1/candidates/123

    Returns full candidate details including attachments and activities
    """
    candidate = Candidate.query_for_site(current_user.site_id).get_or_404(id)

    if candidate.is_admin_hidden:
        return jsonify({'error': 'Candidate not found'}), 404

    # Include related data
    data = candidate_schema.dump(candidate)
    data['attachments'] = [
        {
            'attachment_id': att.attachment_id,
            'title': att.title,
            'original_filename': att.original_filename,
            'file_size': att.file_size,
            'date_created': att.date_created.isoformat() if att.date_created else None
        }
        for att in candidate.attachments
    ]

    return jsonify(data), 200


@api_bp.route('/candidates', methods=['POST'])
@token_required
def create_candidate(current_user):
    """
    Create new candidate

    POST /api/v1/candidates
    {
        "first_name": "John",
        "last_name": "Doe",
        "email1": "john@example.com",
        "phone_cell": "555-1234",
        "key_skills": "Python, Flask, SQL"
    }
    """
    # Check plan limits
    if not current_user.site.can_add_candidate():
        return jsonify({
            'error': 'Maximum candidates reached',
            'message': 'Please upgrade your plan to add more candidates'
        }), 403

    try:
        data = candidate_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400

    # Check duplicates
    if data.get('email1'):
        existing = Candidate.query_for_site(current_user.site_id).filter_by(
            email1=data['email1'],
            is_admin_hidden=False
        ).first()
        if existing:
            return jsonify({
                'error': 'Duplicate candidate',
                'message': 'Candidate with this email already exists',
                'existing_id': existing.candidate_id
            }), 409

    # Create candidate
    candidate = Candidate(site_id=current_user.site_id, **data)
    candidate.owner = current_user.user_id
    candidate.entered_by = current_user.user_id

    db.session.add(candidate)
    db.session.commit()

    # Log activity
    activity = Activity(
        site_id=current_user.site_id,
        data_item_id=candidate.candidate_id,
        data_item_type=100,  # Candidate
        type=300,  # Created
        entered_by=current_user.user_id,
        notes=f'Candidate created via API'
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify(candidate_schema.dump(candidate)), 201


@api_bp.route('/candidates/<int:id>', methods=['PUT'])
@token_required
def update_candidate(current_user, id):
    """
    Update candidate

    PUT /api/v1/candidates/123
    {
        "phone_cell": "555-5678",
        "key_skills": "Python, Flask, SQL, Docker"
    }
    """
    candidate = Candidate.query_for_site(current_user.site_id).get_or_404(id)

    if candidate.is_admin_hidden:
        return jsonify({'error': 'Candidate not found'}), 404

    try:
        data = candidate_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400

    # Update fields
    for key, value in data.items():
        if hasattr(candidate, key):
            setattr(candidate, key, value)

    candidate.date_modified_by = current_user.user_id

    db.session.commit()

    # Log activity
    activity = Activity(
        site_id=current_user.site_id,
        data_item_id=candidate.candidate_id,
        data_item_type=100,
        type=500,  # Modified
        entered_by=current_user.user_id,
        notes=f'Candidate updated via API'
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify(candidate_schema.dump(candidate)), 200


@api_bp.route('/candidates/<int:id>', methods=['DELETE'])
@token_required
def delete_candidate(current_user, id):
    """
    Delete candidate (soft delete)

    DELETE /api/v1/candidates/123
    """
    candidate = Candidate.query_for_site(current_user.site_id).get_or_404(id)

    if candidate.is_admin_hidden:
        return jsonify({'error': 'Candidate not found'}), 404

    # Soft delete
    candidate.is_admin_hidden = True
    candidate.date_modified_by = current_user.user_id

    db.session.commit()

    # Log activity
    activity = Activity(
        site_id=current_user.site_id,
        data_item_id=candidate.candidate_id,
        data_item_type=100,
        type=600,  # Deleted
        entered_by=current_user.user_id,
        notes=f'Candidate deleted via API'
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify({'message': 'Candidate deleted successfully'}), 200


@api_bp.route('/candidates/<int:id>/pipeline', methods=['GET'])
@token_required
def get_candidate_pipeline(current_user, id):
    """
    Get candidate's pipeline entries

    GET /api/v1/candidates/123/pipeline

    Returns all jobs the candidate is associated with and their status
    """
    candidate = Candidate.query_for_site(current_user.site_id).get_or_404(id)

    if candidate.is_admin_hidden:
        return jsonify({'error': 'Candidate not found'}), 404

    entries = CandidateJobOrder.query_for_site(current_user.site_id).filter_by(
        candidate_id=id
    ).all()

    data = []
    for entry in entries:
        item = pipeline_entry_schema.dump(entry)
        item['candidate_name'] = f"{candidate.first_name} {candidate.last_name}"
        item['job_title'] = entry.joborder.title if entry.joborder else None
        data.append(item)

    return jsonify({'data': data}), 200


@api_bp.route('/candidates/<int:id>/pipeline', methods=['POST'])
@token_required
def add_candidate_to_job(current_user, id):
    """
    Add candidate to job pipeline

    POST /api/v1/candidates/123/pipeline
    {
        "joborder_id": 45,
        "status": 200
    }
    """
    candidate = Candidate.query_for_site(current_user.site_id).get_or_404(id)

    if candidate.is_admin_hidden:
        return jsonify({'error': 'Candidate not found'}), 404

    data = request.json

    if not data or not data.get('joborder_id'):
        return jsonify({'error': 'joborder_id is required'}), 400

    # Check if already in pipeline
    existing = CandidateJobOrder.query_for_site(current_user.site_id).filter_by(
        candidate_id=id,
        joborder_id=data['joborder_id']
    ).first()

    if existing:
        return jsonify({
            'error': 'Already in pipeline',
            'message': 'Candidate is already associated with this job'
        }), 409

    # Create pipeline entry
    entry = CandidateJobOrder(
        site_id=current_user.site_id,
        candidate_id=id,
        joborder_id=data['joborder_id'],
        status=data.get('status', 0)
    )

    db.session.add(entry)
    db.session.commit()

    # Log activity
    activity = Activity(
        site_id=current_user.site_id,
        data_item_id=id,
        data_item_type=100,
        type=700,  # Pipeline Change
        entered_by=current_user.user_id,
        notes=f'Added to job pipeline via API'
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify(pipeline_entry_schema.dump(entry)), 201


@api_bp.route('/candidates/<int:id>/activities', methods=['GET'])
@token_required
def get_candidate_activities(current_user, id):
    """
    Get candidate activity history

    GET /api/v1/candidates/123/activities
    """
    candidate = Candidate.query_for_site(current_user.site_id).get_or_404(id)

    if candidate.is_admin_hidden:
        return jsonify({'error': 'Candidate not found'}), 404

    activities = Activity.query_for_site(current_user.site_id).filter_by(
        data_item_id=id,
        data_item_type=100
    ).order_by(Activity.date_created.desc()).limit(50).all()

    data = [
        {
            'activity_id': act.activity_id,
            'type': act.type,
            'notes': act.notes,
            'entered_by': act.entered_by,
            'date_created': act.date_created.isoformat() if act.date_created else None
        }
        for act in activities
    ]

    return jsonify({'data': data}), 200
