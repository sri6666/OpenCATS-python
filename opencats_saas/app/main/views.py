"""
Main Views - Dashboard and Landing Pages
"""
from flask import render_template, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.main import main_bp
from app.models import Candidate, JobOrder, Company, Contact, CandidateJobOrder
from app.extensions import db
from sqlalchemy import func
from datetime import datetime, timedelta


@main_bp.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('main/landing.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    site_id = current_user.site_id

    # Get statistics
    stats = {
        'candidates': Candidate.query_for_site(site_id).filter_by(is_admin_hidden=False).count(),
        'candidates_this_week': get_candidates_this_week(site_id),
        'active_jobs': JobOrder.query_for_site(site_id).filter_by(status=0, is_admin_hidden=False).count(),
        'openings': get_total_openings(site_id),
        'companies': Company.query_for_site(site_id).filter_by(is_admin_hidden=False).count(),
        'contacts': Contact.query_for_site(site_id).filter_by(is_admin_hidden=False).count(),
        'placements_this_month': get_placements_count(site_id, 'month'),
    }

    # Recent activities (placeholder)
    recent_activities = []

    # Hot candidates
    hot_candidates = Candidate.query_for_site(site_id)\
        .filter_by(is_hot=True, is_admin_hidden=False)\
        .order_by(Candidate.date_modified.desc())\
        .limit(5).all()

    # Active job orders (for table display)
    active_jobs = JobOrder.query_for_site(site_id)\
        .filter_by(status=0, is_admin_hidden=False)\
        .order_by(JobOrder.date_created.desc())\
        .limit(10).all()

    # Add pipeline count to jobs
    for job in active_jobs:
        job.pipeline_count = CandidateJobOrder.query_for_site(site_id)\
            .filter_by(joborder_id=job.joborder_id).count()

    return render_template('main/dashboard.html',
                         stats=stats,
                         recent_activities=recent_activities,
                         hot_candidates=hot_candidates,
                         active_jobs=active_jobs)


@main_bp.route('/onboarding')
@login_required
def onboarding():
    """Onboarding wizard for new users"""
    return render_template('main/onboarding.html')


@main_bp.route('/search')
@login_required
def global_search():
    """Global search across all entities"""
    from flask import request
    query = request.args.get('q', '')

    if not query:
        return render_template('main/search.html', query='', results={})

    site_id = current_user.site_id

    # Search candidates
    candidates = Candidate.query_for_site(site_id).filter(
        db.or_(
            Candidate.first_name.like(f'%{query}%'),
            Candidate.last_name.like(f'%{query}%'),
            Candidate.email1.like(f'%{query}%'),
            Candidate.key_skills.like(f'%{query}%')
        )
    ).limit(10).all()

    # Search companies
    companies = Company.query_for_site(site_id).filter(
        Company.name.like(f'%{query}%')
    ).limit(10).all()

    # Search job orders
    jobs = JobOrder.query_for_site(site_id).filter(
        db.or_(
            JobOrder.title.like(f'%{query}%'),
            JobOrder.description.like(f'%{query}%')
        )
    ).limit(10).all()

    results = {
        'candidates': candidates,
        'companies': companies,
        'jobs': jobs
    }

    return render_template('main/search.html', query=query, results=results)


@main_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


# Helper functions

def get_placements_count(site_id, period='month'):
    """Get placements count for period"""
    now = datetime.utcnow()

    if period == 'month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = now - timedelta(days=now.weekday())
    elif period == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = now - timedelta(days=365)

    return CandidateJobOrder.query_for_site(site_id).filter(
        CandidateJobOrder.status == 800,  # Placed status
        CandidateJobOrder.date_modified >= start_date
    ).count()


def get_candidates_this_week(site_id):
    """Get count of candidates added this week"""
    now = datetime.utcnow()
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    return Candidate.query_for_site(site_id).filter(
        Candidate.date_created >= week_start,
        Candidate.is_admin_hidden == False
    ).count()


def get_total_openings(site_id):
    """Get total job openings available"""
    result = db.session.query(func.sum(JobOrder.openings_available)).filter(
        JobOrder.site_id == site_id,
        JobOrder.status == 0,  # Active jobs
        JobOrder.is_admin_hidden == False
    ).scalar()

    return result or 0
