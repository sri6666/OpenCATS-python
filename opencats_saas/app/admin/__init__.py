"""
Admin Blueprint - SaaS Management Dashboard
For managing tenants, users, billing, and system settings
"""
from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

from app.admin import views
