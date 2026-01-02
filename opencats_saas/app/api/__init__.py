"""
API Blueprint - RESTful API with JWT Authentication
"""
from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

from app.api import auth, candidates, joborders, companies, contacts
