"""
Companies Blueprint - Client Management
"""
from flask import Blueprint

companies_bp = Blueprint('companies', __name__)

from app.companies import views
