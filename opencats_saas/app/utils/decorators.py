"""
Custom Decorators
"""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def permission_required(permission):
    """
    Decorator to check if user has required permission

    Usage:
        @permission_required('candidates.view')
        def view_candidates():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))

            if not current_user.has_permission(permission):
                flash('You do not have permission to access this page.', 'danger')
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator to require admin access (level 400+)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))

        if not current_user.is_admin:
            flash('Admin access required.', 'danger')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function


def root_required(f):
    """Decorator to require root access (level 500)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))

        if not current_user.is_root:
            flash('Root access required.', 'danger')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function
