"""
Job Orders Views - Job Management & Pipeline
"""
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.joborders import joborders_bp
from app.joborders.forms import JobOrderForm, JobOrderSearchForm, AddToPipelineForm
from app.models import JobOrder, Candidate, Company, Contact, CandidateJobOrder, Activity
from app.extensions import db
from app.utils.decorators import permission_required
from datetime import datetime


@joborders_bp.route('/')
@login_required
@permission_required('joborders.view')
def index():
    """List all job orders"""
    page = request.args.get('page', 1, type=int)
    per_page = current_user.items_per_page or 20

    # Base query
    query = JobOrder.query_for_site(current_user.site_id)
    query = query.filter_by(is_admin_hidden=False)

    # Filters
    search = request.args.get('search')
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                JobOrder.title.like(search_term),
                JobOrder.description.like(search_term)
            )
        )

    # Status filter
    status = request.args.get('status', type=int)
    if status:
        query = query.filter_by(status=status)
    else:
        # Default: show only active jobs
        query = query.filter_by(status=1)

    # Hot jobs filter
    if request.args.get('hot') == '1':
        query = query.filter_by(is_hot=True)

    # Company filter
    company_id = request.args.get('company_id', type=int)
    if company_id:
        query = query.filter_by(company_id=company_id)

    # Sorting
    sort_by = request.args.get('sort', 'date_modified')
    sort_dir = request.args.get('dir', 'desc')

    if sort_by == 'title':
        order_col = JobOrder.title
    elif sort_by == 'company':
        order_col = Company.name
        query = query.join(JobOrder.company)
    elif sort_by == 'date_created':
        order_col = JobOrder.date_created
    else:
        order_col = JobOrder.date_modified

    if sort_dir == 'desc':
        order_col = order_col.desc()

    query = query.order_by(order_col)

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('joborders/index.html',
                         joborders=pagination.items,
                         pagination=pagination,
                         search=search)


@joborders_bp.route('/<int:id>')
@joborders_bp.route('/view/<int:id>')
@login_required
@permission_required('joborders.view')
def show(id):
    """Show job order details"""
    joborder = JobOrder.query_for_site(current_user.site_id).filter_by(joborder_id=id).first_or_404()

    if joborder.is_admin_hidden:
        flash('Job order not found.', 'warning')
        return redirect(url_for('joborders.index'))

    # Load pipeline entries
    pipeline_entries = joborder.pipeline_entries\
        .join(CandidateJobOrder.candidate)\
        .order_by(CandidateJobOrder.date_modified.desc())\
        .all()

    # Group by status
    pipeline_by_status = {}
    for entry in pipeline_entries:
        status = entry.status
        if status not in pipeline_by_status:
            pipeline_by_status[status] = []
        pipeline_by_status[status].append(entry)

    # Get activities
    activities = Activity.query_for_site(current_user.site_id).filter_by(
        data_item_type=400,  # JobOrder
        data_item_id=joborder.joborder_id
    ).order_by(Activity.date_created.desc()).limit(10).all()

    return render_template('joborders/show.html',
                         joborder=joborder,
                         pipeline_entries=pipeline_entries,
                         pipeline_by_status=pipeline_by_status,
                         activities=activities)


@joborders_bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('joborders.add')
def add():
    """Add new job order"""
    # Check plan limits
    if not current_user.site.can_add_job():
        flash('You have reached the maximum number of job orders for your plan. Please upgrade.', 'warning')
        return redirect(url_for('billing.plans'))

    form = JobOrderForm()

    if form.validate_on_submit():
        # Create job order
        joborder = JobOrder(
            site_id=current_user.site_id,
            entered_by=current_user.user_id,
            owner=current_user.user_id,
            recruiter=current_user.user_id,
            status=1,  # Active
            openings_available=form.openings.data
        )

        # Populate from form
        form.populate_obj(joborder)

        db.session.add(joborder)
        db.session.commit()

        # Log activity
        log_activity(joborder.joborder_id, 400, 'created', current_user.user_id)

        flash(f'Job order "{joborder.title}" created successfully.', 'success')
        return redirect(url_for('joborders.show', id=joborder.joborder_id))

    return render_template('joborders/add.html', form=form)


@joborders_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('joborders.edit')
def edit(id):
    """Edit job order"""
    joborder = JobOrder.query_for_site(current_user.site_id).filter_by(joborder_id=id).first_or_404()

    if joborder.is_admin_hidden:
        flash('Job order not found.', 'warning')
        return redirect(url_for('joborders.index'))

    form = JobOrderForm(obj=joborder)

    if form.validate_on_submit():
        # Track changes
        changes = track_changes(joborder, form)

        # Update job order
        form.populate_obj(joborder)
        joborder.date_modified = datetime.utcnow()

        db.session.commit()

        # Log changes
        if changes:
            log_activity(joborder.joborder_id, 400, f'updated: {", ".join(changes)}', current_user.user_id)

        flash(f'Job order "{joborder.title}" updated successfully.', 'success')
        return redirect(url_for('joborders.show', id=joborder.joborder_id))

    return render_template('joborders/edit.html', form=form, joborder=joborder)


@joborders_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('joborders.delete')
def delete(id):
    """Delete (hide) job order"""
    joborder = JobOrder.query_for_site(current_user.site_id).filter_by(joborder_id=id).first_or_404()

    # Soft delete
    joborder.is_admin_hidden = True
    joborder.date_modified = datetime.utcnow()

    db.session.commit()

    # Log activity
    log_activity(joborder.joborder_id, 400, 'deleted', current_user.user_id)

    flash(f'Job order "{joborder.title}" has been deleted.', 'success')
    return redirect(url_for('joborders.index'))


@joborders_bp.route('/<int:id>/pipeline')
@login_required
@permission_required('joborders.view')
def pipeline(id):
    """View pipeline for job order"""
    joborder = JobOrder.query_for_site(current_user.site_id).filter_by(joborder_id=id).first_or_404()

    # Get pipeline entries grouped by status
    pipeline_entries = joborder.pipeline_entries.all()

    # Status definitions
    statuses = [
        {'id': 0, 'name': 'No Contact', 'color': 'secondary'},
        {'id': 200, 'name': 'Contacted', 'color': 'info'},
        {'id': 250, 'name': 'Candidate Responded', 'color': 'primary'},
        {'id': 300, 'name': 'Qualifying', 'color': 'warning'},
        {'id': 400, 'name': 'Submitted', 'color': 'primary'},
        {'id': 500, 'name': 'Interviewing', 'color': 'info'},
        {'id': 600, 'name': 'Offered', 'color': 'success'},
        {'id': 650, 'name': 'Not in Consideration', 'color': 'danger'},
        {'id': 700, 'name': 'Client Declined', 'color': 'danger'},
        {'id': 800, 'name': 'Placed', 'color': 'success'},
    ]

    # Group candidates by status
    pipeline_by_status = {status['id']: [] for status in statuses}
    for entry in pipeline_entries:
        if entry.status in pipeline_by_status:
            pipeline_by_status[entry.status].append(entry)

    return render_template('joborders/pipeline.html',
                         joborder=joborder,
                         statuses=statuses,
                         pipeline_by_status=pipeline_by_status)


@joborders_bp.route('/<int:job_id>/add-candidate', methods=['GET', 'POST'])
@login_required
@permission_required('joborders.edit')
def add_candidate(job_id):
    """Add candidate to pipeline"""
    joborder = JobOrder.query_for_site(current_user.site_id).filter_by(joborder_id=job_id).first_or_404()
    form = AddToPipelineForm()

    if form.validate_on_submit():
        candidate_id = form.candidate_id.data

        # Check if already in pipeline
        existing = CandidateJobOrder.query.filter_by(
            candidate_id=candidate_id,
            joborder_id=job_id,
            site_id=current_user.site_id
        ).first()

        if existing:
            flash('Candidate is already in the pipeline for this job.', 'warning')
            return redirect(url_for('joborders.pipeline', id=job_id))

        # Create pipeline entry
        pipeline_entry = CandidateJobOrder(
            site_id=current_user.site_id,
            candidate_id=candidate_id,
            joborder_id=job_id,
            status=0,  # No Contact
            submitted_by=current_user.user_id,
            entered_by=current_user.user_id,
            owner=current_user.user_id
        )

        db.session.add(pipeline_entry)
        db.session.commit()

        # Log activity
        candidate = Candidate.query.get(candidate_id)
        log_activity(job_id, 400, f'added candidate: {candidate.full_name}', current_user.user_id)

        flash(f'Candidate added to pipeline.', 'success')
        return redirect(url_for('joborders.pipeline', id=job_id))

    return render_template('joborders/add_candidate.html', form=form, joborder=joborder)


@joborders_bp.route('/pipeline/<int:entry_id>/update-status', methods=['POST'])
@login_required
@permission_required('joborders.edit')
def update_status(entry_id):
    """Update pipeline entry status"""
    entry = CandidateJobOrder.query_for_site(current_user.site_id).filter_by(candidate_joborder_id=entry_id).first_or_404()

    new_status = request.json.get('status', type=int)
    if new_status is None:
        return jsonify({'error': 'Status is required'}), 400

    # Update status
    old_status = entry.status
    entry.status = new_status
    entry.date_modified = datetime.utcnow()

    db.session.commit()

    # Log activity
    status_names = {
        0: 'No Contact', 200: 'Contacted', 250: 'Candidate Responded',
        300: 'Qualifying', 400: 'Submitted', 500: 'Interviewing',
        600: 'Offered', 650: 'Not in Consideration', 700: 'Client Declined',
        800: 'Placed'
    }

    log_activity(
        entry.joborder_id, 400,
        f'moved {entry.candidate.full_name} from {status_names.get(old_status, "Unknown")} to {status_names.get(new_status, "Unknown")}',
        current_user.user_id
    )

    # Update openings if placed
    if new_status == 800 and old_status != 800:  # Placed
        entry.joborder.openings_available -= 1
        if entry.joborder.openings_available <= 0:
            entry.joborder.status = 4  # Filled
        db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Status updated successfully'
    })


@joborders_bp.route('/pipeline/<int:entry_id>/update-rating', methods=['POST'])
@login_required
@permission_required('joborders.edit')
def update_rating(entry_id):
    """Update pipeline entry rating"""
    entry = CandidateJobOrder.query_for_site(current_user.site_id).filter_by(candidate_joborder_id=entry_id).first_or_404()

    rating = request.json.get('rating', type=int)
    if rating is None or rating < -6 or rating > 5:
        return jsonify({'error': 'Rating must be between -6 and 5'}), 400

    entry.rating_value = rating
    entry.date_modified = datetime.utcnow()

    db.session.commit()

    return jsonify({
        'success': True,
        'rating': rating
    })


@joborders_bp.route('/pipeline/<int:entry_id>/remove', methods=['POST'])
@login_required
@permission_required('joborders.delete')
def remove_from_pipeline(entry_id):
    """Remove candidate from pipeline"""
    entry = CandidateJobOrder.query_for_site(current_user.site_id).filter_by(candidate_joborder_id=entry_id).first_or_404()

    candidate_name = entry.candidate.full_name
    job_id = entry.joborder_id

    db.session.delete(entry)
    db.session.commit()

    # Log activity
    log_activity(job_id, 400, f'removed {candidate_name} from pipeline', current_user.user_id)

    flash('Candidate removed from pipeline.', 'success')
    return redirect(url_for('joborders.pipeline', id=job_id))


@joborders_bp.route('/search', methods=['GET', 'POST'])
@login_required
@permission_required('joborders.view')
def search():
    """Advanced job order search"""
    form = JobOrderSearchForm()

    if form.validate_on_submit():
        query = JobOrder.query_for_site(current_user.site_id)
        query = query.filter_by(is_admin_hidden=False)

        if form.title.data:
            query = query.filter(JobOrder.title.like(f'%{form.title.data}%'))

        if form.company_id.data:
            query = query.filter_by(company_id=form.company_id.data)

        if form.status.data is not None:
            query = query.filter_by(status=form.status.data)

        if form.type.data is not None:
            query = query.filter_by(type=form.type.data)

        if form.city.data:
            query = query.filter(JobOrder.city.like(f'%{form.city.data}%'))

        if form.state.data:
            query = query.filter_by(state=form.state.data)

        results = query.limit(100).all()

        return render_template('joborders/search_results.html',
                             form=form,
                             results=results,
                             count=len(results))

    return render_template('joborders/search.html', form=form)


# Helper functions

def track_changes(joborder, form):
    """Track what fields changed"""
    changes = []

    for field in form:
        if field.name not in ['csrf_token', 'submit']:
            old_value = getattr(joborder, field.name, None)
            new_value = field.data

            if old_value != new_value:
                changes.append(field.label.text)

    return changes


def log_activity(data_item_id, data_item_type, action, user_id):
    """Log activity"""
    activity = Activity(
        site_id=current_user.site_id,
        data_item_id=data_item_id,
        data_item_type=data_item_type,
        type=400,  # Other
        notes=action,
        entered_by=user_id,
        owner=user_id
    )
    db.session.add(activity)
    db.session.commit()
