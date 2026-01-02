"""
Main Views - Dashboard and Landing Pages
"""
from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.main import main_bp
from app.models import Candidate, JobOrder, Company, CandidateJobOrder
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
        'total_candidates': Candidate.query_for_site(site_id).filter_by(is_admin_hidden=False).count(),
        'active_jobs': JobOrder.query_for_site(site_id).filter_by(status=1, is_admin_hidden=False).count(),
        'total_companies': Company.query_for_site(site_id).filter_by(is_admin_hidden=False).count(),
        'placements_this_month': get_placements_count(site_id, 'month'),
    }

    # Recent activity
    recent_candidates = Candidate.query_for_site(site_id)\
        .filter_by(is_admin_hidden=False)\
        .order_by(Candidate.date_created.desc())\
        .limit(5).all()

    recent_jobs = JobOrder.query_for_site(site_id)\
        .filter_by(is_admin_hidden=False)\
        .order_by(JobOrder.date_created.desc())\
        .limit(5).all()

    # Hot candidates and jobs
    hot_candidates = Candidate.query_for_site(site_id)\
        .filter_by(is_hot=True, is_admin_hidden=False)\
        .order_by(Candidate.date_modified.desc())\
        .limit(5).all()

    hot_jobs = JobOrder.query_for_site(site_id)\
        .filter_by(is_hot=True, is_admin_hidden=False)\
        .order_by(JobOrder.date_modified.desc())\
        .limit(5).all()

    return render_template('main/dashboard.html',
                         stats=stats,
                         recent_candidates=recent_candidates,
                         recent_jobs=recent_jobs,
                         hot_candidates=hot_candidates,
                         hot_jobs=hot_jobs)


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
