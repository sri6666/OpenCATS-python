"""
Celery Background Tasks for OpenCATS
Handles asynchronous operations like:
- Email sending
- Resume parsing
- Data export
- Report generation
- Cleanup tasks
"""
import os
import csv
from datetime import datetime, timedelta
from flask import render_template
from flask_mail import Message
from celery import Celery
from app import create_app
from app.extensions import db, mail
from app.models import Candidate, JobOrder, Company, Contact, Activity, Attachment, User

# Initialize Celery
celery = Celery(__name__)
app = create_app()
celery.conf.update(app.config)


class ContextTask(celery.Task):
    """Base task that runs within Flask app context"""
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask


# ============================================================================
# Email Tasks
# ============================================================================

@celery.task(name='app.tasks.send_email')
def send_email(subject, recipients, template, **kwargs):
    """
    Send an email using a template

    Args:
        subject: Email subject
        recipients: List of recipient email addresses
        template: Template path (e.g., 'email/welcome.html')
        **kwargs: Template variables
    """
    try:
        html_body = render_template(template, **kwargs)
        msg = Message(
            subject=subject,
            recipients=recipients if isinstance(recipients, list) else [recipients],
            html=html_body,
            sender=app.config.get('MAIL_DEFAULT_SENDER', 'noreply@opencats.com')
        )
        mail.send(msg)
        return {'status': 'sent', 'recipients': recipients}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


@celery.task(name='app.tasks.send_welcome_email')
def send_welcome_email(user_id, site_id):
    """Send welcome email to new user"""
    from app.models import User, Site

    user = User.query.get(user_id)
    site = Site.query.get(site_id)

    if not user or not site:
        return {'status': 'error', 'error': 'User or site not found'}

    return send_email(
        subject=f'Welcome to {site.name} - OpenCATS',
        recipients=[user.email],
        template='email/welcome.html',
        user=user,
        site_name=site.name,
        site_url=f'https://{site.subdomain}.opencats.com',
        login_url=f'https://{site.subdomain}.opencats.com/auth/login'
    )


@celery.task(name='app.tasks.send_password_reset')
def send_password_reset(user_id, reset_token):
    """Send password reset email"""
    from app.models import User

    user = User.query.get(user_id)
    site = user.site if user else None

    if not user or not site:
        return {'status': 'error', 'error': 'User not found'}

    reset_url = f'https://{site.subdomain}.opencats.com/auth/reset-password/{reset_token}'

    return send_email(
        subject='Password Reset Request - OpenCATS',
        recipients=[user.email],
        template='email/password_reset.html',
        user=user,
        site_name=site.name,
        site_url=f'https://{site.subdomain}.opencats.com',
        reset_url=reset_url
    )


@celery.task(name='app.tasks.notify_new_candidate')
def notify_new_candidate(candidate_id, notify_user_ids):
    """Notify users about new candidate"""
    from app.models import Candidate, User

    candidate = Candidate.query.get(candidate_id)
    if not candidate:
        return {'status': 'error', 'error': 'Candidate not found'}

    added_by = User.query.get(candidate.entered_by)
    site = candidate.site

    users = User.query.filter(User.user_id.in_(notify_user_ids)).all()
    recipients = [u.email for u in users if u.email]

    if not recipients:
        return {'status': 'skipped', 'reason': 'No recipients'}

    candidate_url = f'https://{site.subdomain}.opencats.com/candidates/view/{candidate.candidate_id}'

    return send_email(
        subject=f'New Candidate: {candidate.first_name} {candidate.last_name}',
        recipients=recipients,
        template='email/new_candidate.html',
        candidate=candidate,
        added_by=added_by,
        site_name=site.name,
        site_url=f'https://{site.subdomain}.opencats.com',
        candidate_url=candidate_url
    )


# ============================================================================
# Resume Parsing Tasks
# ============================================================================

@celery.task(name='app.tasks.parse_resume')
def parse_resume(attachment_id):
    """
    Parse resume and extract information

    Extracts:
    - Contact information (email, phone)
    - Skills
    - Work experience
    - Education
    """
    from app.utils.resume_parser import ResumeParser

    attachment = Attachment.query.get(attachment_id)
    if not attachment:
        return {'status': 'error', 'error': 'Attachment not found'}

    try:
        parser = ResumeParser(attachment.file_path)
        data = parser.parse()

        # Update candidate with parsed data if applicable
        if attachment.data_item_type == 100 and attachment.data_item_id:  # Candidate
            candidate = Candidate.query.get(attachment.data_item_id)
            if candidate:
                # Update candidate with parsed data
                if not candidate.email1 and data.get('email'):
                    candidate.email1 = data['email']
                if not candidate.phone_cell and data.get('phone'):
                    candidate.phone_cell = data['phone']
                if data.get('skills'):
                    candidate.key_skills = ', '.join(data['skills'][:20])  # Limit to 20 skills

                db.session.commit()

        return {'status': 'success', 'data': data}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


# ============================================================================
# Export Tasks
# ============================================================================

@celery.task(name='app.tasks.export_candidates_csv')
def export_candidates_csv(site_id, filters=None):
    """Export candidates to CSV file"""
    import io

    query = Candidate.query_for_site(site_id)

    # Apply filters if provided
    if filters:
        if filters.get('is_active'):
            query = query.filter_by(is_active=True)
        if filters.get('is_hot'):
            query = query.filter_by(is_hot=True)
        if filters.get('search'):
            search = f"%{filters['search']}%"
            query = query.filter(
                db.or_(
                    Candidate.first_name.like(search),
                    Candidate.last_name.like(search),
                    Candidate.email1.like(search)
                )
            )

    candidates = query.all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'ID', 'First Name', 'Last Name', 'Email', 'Phone',
        'City', 'State', 'Key Skills', 'Current Employer',
        'Is Hot', 'Is Active', 'Date Created'
    ])

    # Write data
    for candidate in candidates:
        writer.writerow([
            candidate.candidate_id,
            candidate.first_name,
            candidate.last_name,
            candidate.email1 or '',
            candidate.phone_cell or candidate.phone_home or '',
            candidate.city or '',
            candidate.state or '',
            candidate.key_skills or '',
            candidate.current_employer or '',
            'Yes' if candidate.is_hot else 'No',
            'Yes' if candidate.is_active else 'No',
            candidate.date_created.strftime('%Y-%m-%d')
        ])

    # Save to file
    filename = f'candidates_export_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
    filepath = os.path.join(app.config.get('UPLOAD_FOLDER', '/tmp'), filename)

    with open(filepath, 'w', newline='') as f:
        f.write(output.getvalue())

    return {'status': 'success', 'filepath': filepath, 'filename': filename, 'count': len(candidates)}


@celery.task(name='app.tasks.export_jobs_csv')
def export_jobs_csv(site_id, filters=None):
    """Export job orders to CSV file"""
    import io

    query = JobOrder.query_for_site(site_id)

    # Apply filters if provided
    if filters:
        if filters.get('status') is not None:
            query = query.filter_by(status=filters['status'])
        if filters.get('is_hot'):
            query = query.filter_by(is_hot=True)

    jobs = query.all()

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'ID', 'Title', 'Company', 'Type', 'City', 'State',
        'Openings', 'Available', 'Status', 'Salary', 'Date Created'
    ])

    # Write data
    for job in jobs:
        writer.writerow([
            job.joborder_id,
            job.title,
            job.company.name if job.company else '',
            job.type,
            job.city or '',
            job.state or '',
            job.openings,
            job.openings_available,
            'Active' if job.status == 0 else 'Inactive',
            job.salary or '',
            job.date_created.strftime('%Y-%m-%d')
        ])

    # Save to file
    filename = f'jobs_export_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
    filepath = os.path.join(app.config.get('UPLOAD_FOLDER', '/tmp'), filename)

    with open(filepath, 'w', newline='') as f:
        f.write(output.getvalue())

    return {'status': 'success', 'filepath': filepath, 'filename': filename, 'count': len(jobs)}


# ============================================================================
# Cleanup Tasks
# ============================================================================

@celery.task(name='app.tasks.cleanup_old_activities')
def cleanup_old_activities(days=365):
    """Delete activity records older than specified days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    deleted = Activity.query.filter(Activity.date_created < cutoff_date).delete()
    db.session.commit()

    return {'status': 'success', 'deleted': deleted, 'cutoff_date': cutoff_date.strftime('%Y-%m-%d')}


@celery.task(name='app.tasks.cleanup_old_attachments')
def cleanup_old_attachments(days=730):
    """Clean up orphaned attachments older than specified days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Find attachments with no associated data item
    orphaned = Attachment.query.filter(
        Attachment.date_created < cutoff_date,
        Attachment.data_item_id == None
    ).all()

    deleted_count = 0
    for attachment in orphaned:
        # Delete file from filesystem
        if os.path.exists(attachment.file_path):
            os.remove(attachment.file_path)
        db.session.delete(attachment)
        deleted_count += 1

    db.session.commit()

    return {'status': 'success', 'deleted': deleted_count}


@celery.task(name='app.tasks.update_storage_usage')
def update_storage_usage(site_id):
    """Calculate and update storage usage for a site"""
    from app.models import Site

    site = Site.query.get(site_id)
    if not site:
        return {'status': 'error', 'error': 'Site not found'}

    # Calculate total storage used by attachments
    attachments = Attachment.query.filter_by(site_id=site_id).all()
    total_bytes = 0

    for attachment in attachments:
        if os.path.exists(attachment.file_path):
            total_bytes += os.path.getsize(attachment.file_path)

    # Convert to MB
    total_mb = total_bytes / (1024 * 1024)

    # Update site
    site.storage_used_mb = round(total_mb, 2)
    db.session.commit()

    return {'status': 'success', 'storage_mb': total_mb}


# ============================================================================
# Periodic Tasks (Configure in celerybeat)
# ============================================================================

@celery.task(name='app.tasks.send_daily_digest')
def send_daily_digest(site_id):
    """Send daily activity digest to admins"""
    from app.models import Site, User

    site = Site.query.get(site_id)
    if not site:
        return {'status': 'error', 'error': 'Site not found'}

    # Get admin users
    admins = User.query.filter_by(site_id=site_id, is_active=True).filter(
        User.access_level >= 400
    ).all()

    if not admins:
        return {'status': 'skipped', 'reason': 'No active admins'}

    # Get today's stats
    today = datetime.utcnow().date()
    candidates_added = Candidate.query.filter(
        Candidate.site_id == site_id,
        db.func.date(Candidate.date_created) == today
    ).count()

    jobs_added = JobOrder.query.filter(
        JobOrder.site_id == site_id,
        db.func.date(JobOrder.date_created) == today
    ).count()

    # TODO: Send digest email to admins
    recipients = [admin.email for admin in admins if admin.email]

    return {
        'status': 'success',
        'recipients': len(recipients),
        'stats': {
            'candidates': candidates_added,
            'jobs': jobs_added
        }
    }


# ============================================================================
# Utility Functions
# ============================================================================

def schedule_task(task_name, *args, countdown=0, **kwargs):
    """Helper function to schedule a task"""
    task = celery.tasks.get(task_name)
    if task:
        return task.apply_async(args=args, kwargs=kwargs, countdown=countdown)
    return None
