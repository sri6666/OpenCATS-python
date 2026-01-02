"""
Job Orders Blueprint - Job Management & Pipeline
"""
from flask import Blueprint

joborders_bp = Blueprint('joborders', __name__)

from app.joborders import views
