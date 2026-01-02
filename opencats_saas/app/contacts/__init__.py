"""
Contacts Blueprint - Contact Management
"""
from flask import Blueprint

contacts_bp = Blueprint('contacts', __name__)

from app.contacts import views
