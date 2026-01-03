"""
Job Orders API Endpoints
"""
from flask import request, jsonify
from app.api import api_bp
from app.api.auth import token_required
from app.api.schemas import (
    joborder_schema, joborders_schema,
    pipeline_entry_schema, pipeline_entries_schema
)
from app.models import JobOrder, CandidateJobOrder, Activity, Company, Contact
from app.extensions import db
from sqlalchemy import or_
from marshmallow import ValidationError


@api_bp.route('/jobs', methods=['GET'])
@token_required
def get_jobs(current_user):
    """
    List job orders with filtering and pagination

    GET /api/v1/jobs?page=1&per_page=20&status=0&hot_only=true

    Query params:
    - status: 0=Active, 1=On Hold, 2=Closed, 3=Canceled, 4=Filled
    - search: Search in title
    - hot_only: true/false
    - company_id: Filter by company
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    query = JobOrder.query_for_site(current_user.site_id).filter_by(is_admin_hidden=False)

    # Status filter
    status = request.args.get('status', type=int)
    if status is not None:
        query = query.filter_by(status=status)

    # Company filter
    company_id = request.args.get('company_id', type=int)
    if company_id:
        query = query.filter_by(company_id=company_id)

    # Search
    search = request.args.get('search')
    if search:
        search_filter = or_(
            JobOrder.title.ilike(f'%{search}%'),
            JobOrder.description.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)

    # Hot jobs only
    if request.args.get('hot_only') == 'true':
        query = query.filter_by(is_hot=True)

    # Public only
    if request.args.get('public_only') == 'true':
        query = query.filter_by(public=True)

    # Sort
    sort_by = request.args.get('sort', 'date_created')
    sort_order = request.args.get('order', 'desc')

    if hasattr(JobOrder, sort_by):
        sort_column = getattr(JobOrder, sort_by)
        if sort_order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Enhance with company names
    items = []
    for job in pagination.items:
        data = joborder_schema.dump(job)
        if job.company:
            data['company_name'] = job.company.name
        if job.contact:
            data['contact_name'] = f"{job.contact.first_name} {job.contact.last_name}"
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


@api_bp.route('/jobs/<int:id>', methods=['GET'])
@token_required
def get_job(current_user, id):
    """
    Get single job order by ID

    GET /api/v1/jobs/123

    Returns full job details including pipeline
    """
    job = JobOrder.query_for_site(current_user.site_id).filter_by(joborder_id=id).first_or_404()

    if job.is_admin_hidden:
        return jsonify({'error': 'Job not found'}), 404

    data = joborder_schema.dump(job)

    # Add company info
    if job.company:
        data['company_name'] = job.company.name
        data['company'] = {
            'company_id': job.company.company_id,
            'name': job.company.name,
            'city': job.company.city,
            'state': job.company.state
        }

    # Add contact info
    if job.contact:
        data['contact_name'] = f"{job.contact.first_name} {job.contact.last_name}"
        data['contact'] = {
            'contact_id': job.contact.contact_id,
            'first_name': job.contact.first_name,
            'last_name': job.contact.last_name,
            'email1': job.contact.email1,
            'phone_work': job.contact.phone_work
        }

    return jsonify(data), 200


@api_bp.route('/jobs', methods=['POST'])
@token_required
def create_job(current_user):
    """
    Create new job order

    POST /api/v1/jobs
    {
        "company_id": 10,
        "contact_id": 15,
        "title": "Senior Python Developer",
        "type": 1,
        "status": 0,
        "openings": 2,
        "description": "Looking for experienced Python developer..."
    }
    """
    # Check plan limits
    if not current_user.site.can_add_job():
        return jsonify({
            'error': 'Maximum jobs reached',
            'message': 'Please upgrade your plan to add more job orders'
        }), 403

    try:
        data = joborder_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400

    # Verify company exists
    company = Company.query_for_site(current_user.site_id).get(data['company_id'])
    if not company:
        return jsonify({'error': 'Company not found'}), 404

    # Create job
    job = JobOrder(site_id=current_user.site_id, **data)
    job.owner = current_user.user_id
    job.entered_by = current_user.user_id

    # Set openings_available
    if job.openings:
        job.openings_available = job.openings

    db.session.add(job)
    db.session.commit()

    # Log activity
    activity = Activity(
        site_id=current_user.site_id,
        data_item_id=job.joborder_id,
        data_item_type=200,  # Job Order
        type=300,  # Created
        entered_by=current_user.user_id,
        notes=f'Job order created via API'
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify(joborder_schema.dump(job)), 201


@api_bp.route('/jobs/<int:id>', methods=['PUT'])
@token_required
def update_job(current_user, id):
    """
    Update job order

    PUT /api/v1/jobs/123
    {
        "status": 1,
        "notes": "Put on hold pending budget approval"
    }
    """
    job = JobOrder.query_for_site(current_user.site_id).filter_by(joborder_id=id).first_or_404()

    if job.is_admin_hidden:
        return jsonify({'error': 'Job not found'}), 404

    try:
        data = joborder_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400

    # Update fields
    for key, value in data.items():
        if hasattr(job, key):
            setattr(job, key, value)

    job.date_modified_by = current_user.user_id

    db.session.commit()

    # Log activity
    activity = Activity(
        site_id=current_user.site_id,
        data_item_id=job.joborder_id,
        data_item_type=200,
        type=500,  # Modified
        entered_by=current_user.user_id,
        notes=f'Job order updated via API'
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify(joborder_schema.dump(job)), 200


@api_bp.route('/jobs/<int:id>', methods=['DELETE'])
@token_required
def delete_job(current_user, id):
    """
    Delete job order (soft delete)

    DELETE /api/v1/jobs/123
    """
    job = JobOrder.query_for_site(current_user.site_id).filter_by(joborder_id=id).first_or_404()

    if job.is_admin_hidden:
        return jsonify({'error': 'Job not found'}), 404

    # Soft delete
    job.is_admin_hidden = True
    job.date_modified_by = current_user.user_id

    db.session.commit()

    # Log activity
    activity = Activity(
        site_id=current_user.site_id,
        data_item_id=job.joborder_id,
        data_item_type=200,
        type=600,  # Deleted
        entered_by=current_user.user_id,
        notes=f'Job order deleted via API'
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify({'message': 'Job order deleted successfully'}), 200


@api_bp.route('/jobs/<int:id>/pipeline', methods=['GET'])
@token_required
def get_job_pipeline(current_user, id):
    """
    Get job's pipeline (all candidates)

    GET /api/v1/jobs/123/pipeline?status=400

    Query params:
    - status: Filter by pipeline status (0, 200, 250, 300, 400, 500, 600, 800)
    """
    job = JobOrder.query_for_site(current_user.site_id).filter_by(joborder_id=id).first_or_404()

    if job.is_admin_hidden:
        return jsonify({'error': 'Job not found'}), 404

    query = CandidateJobOrder.query_for_site(current_user.site_id).filter_by(
        joborder_id=id
    )

    # Status filter
    status = request.args.get('status', type=int)
    if status is not None:
        query = query.filter_by(status=status)

    entries = query.order_by(CandidateJobOrder.status.desc()).all()

    # Group by status
    pipeline = {}
    for entry in entries:
        status_key = entry.status
        if status_key not in pipeline:
            pipeline[status_key] = []

        item = pipeline_entry_schema.dump(entry)
        if entry.candidate:
            item['candidate_name'] = f"{entry.candidate.first_name} {entry.candidate.last_name}"
            item['candidate_email'] = entry.candidate.email1
        item['job_title'] = job.title

        pipeline[status_key].append(item)

    # Format response
    data = []
    status_names = {
        0: 'No Contact',
        200: 'Contacted',
        250: 'Candidate Responded',
        300: 'Qualifying',
        400: 'Submitted',
        500: 'Interviewing',
        600: 'Offered',
        650: 'Offer Accepted',
        700: 'Declined Offer',
        800: 'Placed'
    }

    for status_code, entries in pipeline.items():
        data.append({
            'status': status_code,
            'status_name': status_names.get(status_code, 'Unknown'),
            'count': len(entries),
            'candidates': entries
        })

    # Sort by status code
    data.sort(key=lambda x: x['status'])

    return jsonify({'data': data, 'total_candidates': len(entries)}), 200


@api_bp.route('/jobs/<int:id>/pipeline/<int:entry_id>/status', methods=['PUT'])
@token_required
def update_pipeline_status(current_user, id, entry_id):
    """
    Update candidate status in pipeline

    PUT /api/v1/jobs/123/pipeline/456/status
    {
        "status": 400,
        "notes": "Submitted to hiring manager"
    }
    """
    job = JobOrder.query_for_site(current_user.site_id).filter_by(joborder_id=id).first_or_404()
    entry = CandidateJobOrder.query_for_site(current_user.site_id).filter_by(candidate_joborder_id=entry_id).first_or_404()

    if entry.joborder_id != id:
        return jsonify({'error': 'Pipeline entry does not belong to this job'}), 400

    data = request.json
    new_status = data.get('status')

    if new_status is None:
        return jsonify({'error': 'status is required'}), 400

    # Valid status codes
    valid_statuses = [0, 200, 250, 300, 400, 500, 600, 650, 700, 800]
    if new_status not in valid_statuses:
        return jsonify({'error': 'Invalid status code'}), 400

    entry.status = new_status

    # Auto-update openings when placed
    if new_status == 800 and job.openings_available > 0:
        job.openings_available -= 1
        if job.openings_available == 0:
            job.status = 4  # Filled

    db.session.commit()

    # Log activity
    activity = Activity(
        site_id=current_user.site_id,
        data_item_id=entry.candidate_id,
        data_item_type=100,
        type=700,  # Pipeline Change
        entered_by=current_user.user_id,
        notes=data.get('notes', f'Status changed to {new_status}')
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify(pipeline_entry_schema.dump(entry)), 200


@api_bp.route('/jobs/<int:id>/activities', methods=['GET'])
@token_required
def get_job_activities(current_user, id):
    """
    Get job activity history

    GET /api/v1/jobs/123/activities
    """
    job = JobOrder.query_for_site(current_user.site_id).filter_by(joborder_id=id).first_or_404()

    if job.is_admin_hidden:
        return jsonify({'error': 'Job not found'}), 404

    activities = Activity.query_for_site(current_user.site_id).filter_by(
        data_item_id=id,
        data_item_type=200
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
