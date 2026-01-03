"""
Candidates Views - Complete CRUD Operations
"""
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.candidates import candidates_bp
from app.candidates.forms import CandidateForm, CandidateSearchForm
from app.models import Candidate, CandidateJobOrder, Attachment, Activity
from app.extensions import db
from app.utils.decorators import permission_required
from app.utils.file_handler import save_upload, allowed_file
from werkzeug.utils import secure_filename
from datetime import datetime


@candidates_bp.route('/')
@login_required
@permission_required('candidates.view')
def index():
    """List all candidates with pagination and filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = current_user.items_per_page or 20

    # Base query
    query = Candidate.query_for_site(current_user.site_id)
    query = query.filter_by(is_admin_hidden=False)

    # Apply filters
    search = request.args.get('search')
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Candidate.first_name.like(search_term),
                Candidate.last_name.like(search_term),
                Candidate.email1.like(search_term),
                Candidate.email2.like(search_term),
                Candidate.phone_cell.like(search_term)
            )
        )

    # Filter by hot candidates
    if request.args.get('hot') == '1':
        query = query.filter_by(is_hot=True)

    # Filter by source
    source = request.args.get('source')
    if source:
        query = query.filter_by(source=source)

    # Sorting
    sort_by = request.args.get('sort', 'date_modified')
    sort_dir = request.args.get('dir', 'desc')

    if sort_by == 'name':
        order_col = Candidate.last_name
    elif sort_by == 'date_created':
        order_col = Candidate.date_created
    else:
        order_col = Candidate.date_modified

    if sort_dir == 'desc':
        order_col = order_col.desc()

    query = query.order_by(order_col)

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('candidates/index.html',
                         candidates=pagination.items,
                         pagination=pagination,
                         search=search)


@candidates_bp.route('/<int:id>')
@candidates_bp.route('/view/<int:id>')
@login_required
@permission_required('candidates.view')
def show(id):
    """Show candidate details"""
    candidate = Candidate.query_for_site(current_user.site_id).get_or_404(id)

    if candidate.is_admin_hidden:
        flash('Candidate not found.', 'warning')
        return redirect(url_for('candidates.index'))

    # Load related data
    pipeline_entries = candidate.pipeline_entries\
        .join(CandidateJobOrder.joborder)\
        .order_by(CandidateJobOrder.date_modified.desc())\
        .all()

    attachments = candidate.attachments.all()

    activities = Activity.query_for_site(current_user.site_id).filter_by(
        data_item_type=100,  # Candidate
        data_item_id=candidate.candidate_id
    ).order_by(Activity.date_created.desc()).limit(10).all()

    return render_template('candidates/show.html',
                         candidate=candidate,
                         pipeline_entries=pipeline_entries,
                         attachments=attachments,
                         activities=activities)


@candidates_bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('candidates.add')
def add():
    """Add new candidate"""
    # Check plan limits
    if not current_user.site.can_add_candidate():
        flash('You have reached the maximum number of candidates for your plan. Please upgrade.', 'warning')
        return redirect(url_for('billing.plans'))

    form = CandidateForm()

    if form.validate_on_submit():
        # Check for duplicates
        duplicates = check_duplicates(
            form.email1.data,
            form.phone_cell.data,
            current_user.site_id
        )

        if duplicates and not request.form.get('ignore_duplicates'):
            return render_template('candidates/duplicates.html',
                                 form=form,
                                 duplicates=duplicates)

        # Create candidate
        candidate = Candidate(
            site_id=current_user.site_id,
            entered_by=current_user.user_id,
            owner=current_user.user_id
        )

        # Populate from form
        form.populate_obj(candidate)

        db.session.add(candidate)
        db.session.commit()

        # Log activity
        log_activity(candidate.candidate_id, 100, 'created', current_user.user_id)

        flash(f'Candidate {candidate.full_name} added successfully.', 'success')
        return redirect(url_for('candidates.show', id=candidate.candidate_id))

    return render_template('candidates/add.html', form=form)


@candidates_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('candidates.edit')
def edit(id):
    """Edit candidate"""
    candidate = Candidate.query_for_site(current_user.site_id).get_or_404(id)

    if candidate.is_admin_hidden:
        flash('Candidate not found.', 'warning')
        return redirect(url_for('candidates.index'))

    form = CandidateForm(obj=candidate)

    if form.validate_on_submit():
        # Track changes for history
        changes = track_changes(candidate, form)

        # Update candidate
        form.populate_obj(candidate)
        candidate.date_modified = datetime.utcnow()

        db.session.commit()

        # Log changes
        if changes:
            log_activity(candidate.candidate_id, 100, f'updated: {", ".join(changes)}', current_user.user_id)

        flash(f'Candidate {candidate.full_name} updated successfully.', 'success')
        return redirect(url_for('candidates.show', id=candidate.candidate_id))

    return render_template('candidates/edit.html', form=form, candidate=candidate)


@candidates_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('candidates.delete')
def delete(id):
    """Delete (hide) candidate"""
    candidate = Candidate.query_for_site(current_user.site_id).get_or_404(id)

    # Soft delete
    candidate.is_admin_hidden = True
    candidate.date_modified = datetime.utcnow()

    db.session.commit()

    # Log activity
    log_activity(candidate.candidate_id, 100, 'deleted', current_user.user_id)

    flash(f'Candidate {candidate.full_name} has been deleted.', 'success')
    return redirect(url_for('candidates.index'))


@candidates_bp.route('/<int:id>/upload-resume', methods=['POST'])
@login_required
@permission_required('candidates.edit')
def upload_resume(id):
    """Upload resume for candidate"""
    candidate = Candidate.query_for_site(current_user.site_id).get_or_404(id)

    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['resume']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    # Save file
    filename, file_path, file_size = save_upload(
        file,
        current_user.site_id,
        'resumes'
    )

    # Create attachment record
    attachment = Attachment(
        site_id=current_user.site_id,
        data_item_type=100,  # Candidate
        data_item_id=candidate.candidate_id,
        title='Resume',
        original_filename=file.filename,
        stored_filename=filename,
        file_size=file_size,
        mime_type=file.content_type,
        is_resume=True,
        storage_type='local',  # or 's3' if using S3
        storage_path=file_path,
        entered_by=current_user.user_id,
        owner=current_user.user_id
    )

    db.session.add(attachment)

    # Parse resume text
    from app.utils.resume_parser import extract_text, parse_resume
    try:
        text = extract_text(file_path)
        attachment.text_resume = text

        # Auto-populate fields if empty
        parsed_data = parse_resume(text)
        if parsed_data and not candidate.key_skills:
            if parsed_data.get('skills'):
                candidate.key_skills = ', '.join(parsed_data['skills'])
    except Exception as e:
        # Log error but don't fail
        print(f"Resume parsing error: {e}")

    db.session.commit()

    # Update storage quota
    current_user.site.storage_used_mb += file_size // (1024 * 1024)
    db.session.commit()

    flash('Resume uploaded successfully.', 'success')
    return redirect(url_for('candidates.show', id=id))


@candidates_bp.route('/search', methods=['GET', 'POST'])
@login_required
@permission_required('candidates.view')
def search():
    """Advanced candidate search"""
    form = CandidateSearchForm()

    if form.validate_on_submit():
        # Build query
        query = Candidate.query_for_site(current_user.site_id)
        query = query.filter_by(is_admin_hidden=False)

        if form.name.data:
            name_term = f'%{form.name.data}%'
            query = query.filter(
                db.or_(
                    Candidate.first_name.like(name_term),
                    Candidate.last_name.like(name_term)
                )
            )

        if form.email.data:
            email_term = f'%{form.email.data}%'
            query = query.filter(
                db.or_(
                    Candidate.email1.like(email_term),
                    Candidate.email2.like(email_term)
                )
            )

        if form.phone.data:
            phone_term = f'%{form.phone.data}%'
            query = query.filter(
                db.or_(
                    Candidate.phone_cell.like(phone_term),
                    Candidate.phone_work.like(phone_term),
                    Candidate.phone_home.like(phone_term)
                )
            )

        if form.skills.data:
            skills_term = f'%{form.skills.data}%'
            query = query.filter(Candidate.key_skills.like(skills_term))

        if form.city.data:
            query = query.filter(Candidate.city.like(f'%{form.city.data}%'))

        if form.state.data:
            query = query.filter_by(state=form.state.data)

        results = query.limit(100).all()

        return render_template('candidates/search_results.html',
                             form=form,
                             results=results,
                             count=len(results))

    return render_template('candidates/search.html', form=form)


# Helper functions

def check_duplicates(email, phone, site_id):
    """Check for duplicate candidates by email or phone"""
    duplicates = []

    if email:
        email_dupes = Candidate.query_for_site(site_id).filter(
            db.or_(
                Candidate.email1 == email,
                Candidate.email2 == email
            ),
            Candidate.is_admin_hidden == False
        ).all()
        duplicates.extend(email_dupes)

    if phone:
        # Clean phone number
        phone_clean = ''.join(filter(str.isdigit, phone))
        if len(phone_clean) >= 10:
            phone_pattern = f'%{phone_clean[-10:]}%'
            phone_dupes = Candidate.query_for_site(site_id).filter(
                db.or_(
                    Candidate.phone_cell.like(phone_pattern),
                    Candidate.phone_work.like(phone_pattern),
                    Candidate.phone_home.like(phone_pattern)
                ),
                Candidate.is_admin_hidden == False
            ).all()
            duplicates.extend(phone_dupes)

    # Remove duplicates from list
    return list(set(duplicates))


def track_changes(candidate, form):
    """Track what fields changed"""
    changes = []

    for field in form:
        if field.name not in ['csrf_token', 'submit']:
            old_value = getattr(candidate, field.name, None)
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
