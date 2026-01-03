"""
Audit logging utilities
"""
from app.models import Activity
from app.extensions import db


def log_login(user_id, ip_address, user_agent):
    """Log user login activity"""
    # Simple implementation - just create an activity record
    # In production, you might want a dedicated audit_log table
    try:
        activity = Activity(
            data_item_id=user_id,
            data_item_type=1,  # User
            type=100,  # Login
            entered_by=user_id,
            notes=f'Login from {ip_address}'
        )
        db.session.add(activity)
        db.session.commit()
    except Exception:
        # Don't let audit logging break the login flow
        pass
