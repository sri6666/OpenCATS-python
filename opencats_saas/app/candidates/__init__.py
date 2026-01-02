"""
Candidates Blueprint - Applicant Tracking
"""
from flask import Blueprint

candidates_bp = Blueprint('candidates', __name__)

from app.candidates import views
