"""
Authentication Views - Login, Registration, Tenant Signup
"""
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from app.auth import auth_bp
from app.auth.forms import LoginForm, SignupForm, TenantRegistrationForm
from app.models import User, Site
from app.extensions import db, limiter
from datetime import datetime, timedelta


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        # Find user by username or email
        user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.username.data)
        ).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))

        if not user.is_active:
            flash('Your account has been disabled. Please contact your administrator.', 'warning')
            return redirect(url_for('auth.login'))

        # Check if user's site is active
        if not user.site.is_active:
            flash('Your organization account is inactive. Please contact support.', 'warning')
            return redirect(url_for('auth.login'))

        # Check subscription status
        if user.site.subscription_status not in ['trial', 'active']:
            flash('Your subscription has expired. Please update your payment information.', 'warning')
            return redirect(url_for('billing.subscription'))

        # Log user in
        login_user(user, remember=form.remember_me.data)

        # Update last login
        user.last_login = datetime.utcnow()
        user.last_activity = datetime.utcnow()
        db.session.commit()

        # Log login activity
        from app.utils.audit import log_login
        log_login(user, request.remote_addr, request.user_agent.string)

        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.dashboard')

        flash(f'Welcome back, {user.first_name or user.username}!', 'success')
        return redirect(next_page)

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Tenant registration - Sign up for new account"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = TenantRegistrationForm()

    if form.validate_on_submit():
        # Check if subdomain is available
        existing_site = Site.query.filter_by(subdomain=form.subdomain.data).first()
        if existing_site:
            flash('That subdomain is already taken. Please choose another.', 'danger')
            return redirect(url_for('auth.signup'))

        # Check if email is already registered
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('That email address is already registered.', 'danger')
            return redirect(url_for('auth.login'))

        # Create new site (tenant)
        site = Site(
            name=form.company_name.data,
            subdomain=form.subdomain.data,
            subscription_plan='starter',  # Default plan
            subscription_status='trial',  # Start with trial
            trial_ends_at=datetime.utcnow() + timedelta(days=14),  # 14-day trial
            is_active=True
        )
        db.session.add(site)
        db.session.flush()  # Get site_id

        # Create admin user for the site
        admin_user = User(
            site_id=site.site_id,
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            access_level=400,  # Site Administrator
            is_active=True
        )
        admin_user.set_password(form.password.data)
        db.session.add(admin_user)
        db.session.commit()

        # Send welcome email
        from app.utils.email import send_welcome_email
        send_welcome_email(admin_user, site)

        # Log them in automatically
        login_user(admin_user)

        flash(f'Welcome to OpenCATS! Your 14-day trial has started.', 'success')
        return redirect(url_for('main.onboarding'))

    return render_template('auth/signup.html', form=form)


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def forgot_password():
    """Request password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    from app.auth.forms import ForgotPasswordForm
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            # Generate reset token
            from app.utils.tokens import generate_reset_token
            token = generate_reset_token(user.user_id)

            # Send reset email
            from app.utils.email import send_password_reset_email
            send_password_reset_email(user, token)

        # Always show success message (don't reveal if email exists)
        flash('If that email address is registered, you will receive password reset instructions.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    # Verify token
    from app.utils.tokens import verify_reset_token
    user_id = verify_reset_token(token)

    if user_id is None:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.get(user_id)
    if not user:
        flash('Invalid reset link.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    from app.auth.forms import ResetPasswordForm
    form = ResetPasswordForm()

    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()

        flash('Your password has been reset. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password for logged-in user"""
    from app.auth.forms import ChangePasswordForm
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('auth.change_password'))

        current_user.set_password(form.new_password.data)
        db.session.commit()

        flash('Your password has been changed successfully.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/change_password.html', form=form)
