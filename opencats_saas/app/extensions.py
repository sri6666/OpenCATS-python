"""
Flask Extensions
Centralized initialization of all Flask extensions
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from celery import Celery

# Database
db = SQLAlchemy()

# Migrations
migrate = Migrate()

# Authentication
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Email
mail = Mail()

# CSRF Protection
csrf = CSRFProtect()

# Rate Limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://localhost:6379/2"
)

# Caching
cache = Cache()

# Celery Task Queue
celery_app = Celery(
    'opencats',
    broker='redis://localhost:6379/1',
    backend='redis://localhost:6379/1'
)


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    from app.models import User
    return User.query.get(int(user_id))
