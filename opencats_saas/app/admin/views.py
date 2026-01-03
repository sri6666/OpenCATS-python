"""
Admin Views - SaaS Management Dashboard
Tenant management, user administration, billing overview, system analytics
"""
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.admin import admin_bp
from app.models import Site, User, Candidate, JobOrder, Company
from app.extensions import db
from app.utils.decorators import admin_required, root_required
from sqlalchemy import func
from datetime import datetime, timedelta


@admin_bp.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard"""
    site_id = current_user.site_id

    # Get site information
    site = Site.query.filter_by(site_id=site_id).first_or_404()

    # Usage statistics
    stats = {
        'users': User.query_for_site(site_id).filter_by(is_active=True).count(),
        'candidates': Candidate.query_for_site(site_id).filter_by(is_admin_hidden=False).count(),
        'jobs': JobOrder.query_for_site(site_id).filter_by(is_admin_hidden=False).count(),
        'companies': Company.query_for_site(site_id).filter_by(is_admin_hidden=False).count(),
        'storage_used_mb': site.storage_used_mb,
    }

    # Plan limits
    from config import Config
    plan = Config.SUBSCRIPTION_PLANS.get(site.subscription_plan, {})
    limits = plan.get('features', {})

    # Usage percentages
    usage = {
        'users': calculate_usage(stats['users'], limits.get('max_users', -1)),
        'candidates': calculate_usage(stats['candidates'], limits.get('max_candidates', -1)),
        'jobs': calculate_usage(stats['jobs'], limits.get('max_jobs', -1)),
        'storage': calculate_usage(stats['storage_used_mb'], limits.get('storage_gb', 0) * 1024),
    }

    # Recent users
    recent_users = User.query_for_site(site_id)\
        .order_by(User.date_created.desc())\
        .limit(5).all()

    # Trial status
    trial_days_left = None
    if site.subscription_status == 'trial' and site.trial_ends_at:
        trial_days_left = (site.trial_ends_at - datetime.utcnow()).days

    return render_template('admin/index.html',
                         site=site,
                         stats=stats,
                         limits=limits,
                         usage=usage,
                         recent_users=recent_users,
                         trial_days_left=trial_days_left)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Manage users"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = User.query_for_site(current_user.site_id)

    # Filter
    status = request.args.get('status')
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)

    pagination = query.order_by(User.date_created.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template('admin/users.html',
                         users=pagination.items,
                         pagination=pagination)


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Enable/disable user"""
    user = User.query_for_site(current_user.site_id).filter_by(user_id=user_id).first_or_404()

    # Can't disable yourself
    if user.user_id == current_user.user_id:
        flash('You cannot disable your own account.', 'danger')
        return redirect(url_for('admin.users'))

    user.is_active = not user.is_active
    db.session.commit()

    status = 'enabled' if user.is_active else 'disabled'
    flash(f'User {user.username} has been {status}.', 'success')

    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/change-access', methods=['POST'])
@login_required
@admin_required
def change_user_access(user_id):
    """Change user access level"""
    user = User.query_for_site(current_user.site_id).filter_by(user_id=user_id).first_or_404()

    new_level = request.form.get('access_level', type=int)

    # Validate access level
    valid_levels = [100, 200, 300, 400]
    if new_level not in valid_levels:
        flash('Invalid access level.', 'danger')
        return redirect(url_for('admin.users'))

    # Root users can only be changed by root
    if user.access_level == 500 and not current_user.is_root:
        flash('Only root users can modify root access.', 'danger')
        return redirect(url_for('admin.users'))

    # Can't change your own access level
    if user.user_id == current_user.user_id:
        flash('You cannot change your own access level.', 'danger')
        return redirect(url_for('admin.users'))

    user.access_level = new_level
    db.session.commit()

    flash(f'Access level updated for {user.username}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/billing')
@login_required
@admin_required
def billing():
    """Billing and subscription management"""
    site = Site.query.filter_by(site_id=current_user.site_id).first_or_404()

    # Get current plan
    from config import Config
    current_plan = Config.SUBSCRIPTION_PLANS.get(site.subscription_plan, {})
    all_plans = Config.SUBSCRIPTION_PLANS

    # Calculate monthly cost
    monthly_cost = current_plan.get('price', 0)

    # Trial info
    trial_days_left = None
    if site.subscription_status == 'trial' and site.trial_ends_at:
        trial_days_left = (site.trial_ends_at - datetime.utcnow()).days

    return render_template('admin/billing.html',
                         site=site,
                         current_plan=current_plan,
                         all_plans=all_plans,
                         monthly_cost=monthly_cost,
                         trial_days_left=trial_days_left)


@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    """Site settings"""
    site = Site.query.filter_by(site_id=current_user.site_id).first_or_404()

    return render_template('admin/settings.html', site=site)


@admin_bp.route('/settings/update', methods=['POST'])
@login_required
@admin_required
def update_settings():
    """Update site settings"""
    site = Site.query.filter_by(site_id=current_user.site_id).first_or_404()

    site.name = request.form.get('site_name', site.name)
    site.timezone = request.form.get('timezone', site.timezone)
    site.date_format = request.form.get('date_format', site.date_format)

    db.session.commit()

    flash('Settings updated successfully.', 'success')
    return redirect(url_for('admin.settings'))


@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Usage analytics and reports"""
    site_id = current_user.site_id

    # Activity over time (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    # New candidates per week
    candidates_data = db.session.query(
        func.date(Candidate.date_created).label('date'),
        func.count(Candidate.candidate_id).label('count')
    ).filter(
        Candidate.site_id == site_id,
        Candidate.date_created >= thirty_days_ago
    ).group_by(func.date(Candidate.date_created)).all()

    # New jobs per week
    jobs_data = db.session.query(
        func.date(JobOrder.date_created).label('date'),
        func.count(JobOrder.joborder_id).label('count')
    ).filter(
        JobOrder.site_id == site_id,
        JobOrder.date_created >= thirty_days_ago
    ).group_by(func.date(JobOrder.date_created)).all()

    # User activity
    user_activity = db.session.query(
        User.username,
        User.last_activity
    ).filter(
        User.site_id == site_id,
        User.is_active == True
    ).order_by(User.last_activity.desc()).limit(10).all()

    return render_template('admin/analytics.html',
                         candidates_data=candidates_data,
                         jobs_data=jobs_data,
                         user_activity=user_activity)


# Root-only views

@admin_bp.route('/all-tenants')
@login_required
@root_required
def all_tenants():
    """View all tenants (root only)"""
    page = request.args.get('page', 1, type=int)
    per_page = 50

    query = Site.query.filter_by(is_deleted=False)

    # Filter by status
    status = request.args.get('status')
    if status:
        query = query.filter_by(subscription_status=status)

    # Sort
    sort_by = request.args.get('sort', 'date_created')
    if sort_by == 'name':
        query = query.order_by(Site.name)
    else:
        query = query.order_by(Site.date_created.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Calculate total revenue
    from config import Config
    total_revenue = 0
    for site in pagination.items:
        if site.subscription_status == 'active':
            plan = Config.SUBSCRIPTION_PLANS.get(site.subscription_plan, {})
            total_revenue += plan.get('price', 0)

    return render_template('admin/all_tenants.html',
                         sites=pagination.items,
                         pagination=pagination,
                         total_revenue=total_revenue)


@admin_bp.route('/tenant/<int:site_id>/impersonate', methods=['POST'])
@login_required
@root_required
def impersonate_tenant(site_id):
    """Impersonate a tenant (root only)"""
    site = Site.query.filter_by(site_id=site_id).first_or_404()

    # Get or create admin user for this site
    admin_user = User.query.filter_by(site_id=site_id, access_level=500).first()

    if not admin_user:
        flash('No admin user found for this tenant.', 'warning')
        return redirect(url_for('admin.all_tenants'))

    # Log in as that user
    from flask_login import login_user
    login_user(admin_user)

    flash(f'Now impersonating {site.name}', 'info')
    return redirect(url_for('main.dashboard'))


# Helper functions

def calculate_usage(used, limit):
    """Calculate usage percentage"""
    if limit == -1:  # Unlimited
        return 0
    if limit == 0:
        return 100
    return min(100, int((used / limit) * 100))
