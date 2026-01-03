"""
Configuration for OpenCATS SaaS Application
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables (skip if testing)
basedir = os.path.abspath(os.path.dirname(__file__))
if not os.environ.get('TESTING'):
    load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Base configuration"""

    # Application
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-CHANGE-IN-PRODUCTION'
    APP_NAME = 'OpenCATS'
    APP_VERSION = '2.0.0'

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://cats:password@localhost/opencats_saas'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_RECYCLE = 3600

    # Session
    SESSION_TYPE = 'redis'
    SESSION_REDIS = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True  # HTTPS only in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    BCRYPT_LOG_ROUNDS = 12

    # Email (AWS SES or SMTP)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'email-smtp.us-east-1.amazonaws.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@opencats.app'

    # File Uploads
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'rtf', 'txt', 'odt', 'jpg', 'jpeg', 'png', 'gif'}

    # AWS S3 (for production file storage)
    USE_S3 = os.environ.get('USE_S3', 'false').lower() in ['true', 'on', '1']
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET') or 'opencats-uploads'
    AWS_S3_REGION = os.environ.get('AWS_S3_REGION') or 'us-east-1'

    # Celery (Background Tasks)
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/1'

    # Elasticsearch
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL') or 'http://localhost:9200'
    ELASTICSEARCH_INDEX_PREFIX = 'opencats'

    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/2'
    RATELIMIT_ENABLED = True

    # Pagination
    ITEMS_PER_PAGE = 20
    MAX_ITEMS_PER_PAGE = 100

    # SaaS Settings
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

    # Subscription Plans
    SUBSCRIPTION_PLANS = {
        'starter': {
            'name': 'Starter',
            'price': 49,
            'currency': 'usd',
            'interval': 'month',
            'features': {
                'max_users': 3,
                'max_candidates': 500,
                'max_jobs': 20,
                'storage_gb': 5,
                'api_access': False,
                'custom_domain': False
            }
        },
        'professional': {
            'name': 'Professional',
            'price': 99,
            'currency': 'usd',
            'interval': 'month',
            'features': {
                'max_users': 10,
                'max_candidates': 2000,
                'max_jobs': 100,
                'storage_gb': 20,
                'api_access': True,
                'custom_domain': True
            }
        },
        'enterprise': {
            'name': 'Enterprise',
            'price': 249,
            'currency': 'usd',
            'interval': 'month',
            'features': {
                'max_users': -1,  # unlimited
                'max_candidates': -1,
                'max_jobs': -1,
                'storage_gb': 100,
                'api_access': True,
                'custom_domain': True,
                'priority_support': True
            }
        }
    }

    # Multi-tenancy
    TENANT_SUBDOMAIN_ENABLED = True
    TENANT_CUSTOM_DOMAIN_ENABLED = True

    # Monitoring (Sentry)
    SENTRY_DSN = os.environ.get('SENTRY_DSN')

    # Cache
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/3'
    CACHE_DEFAULT_TIMEOUT = 300


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False
    WTF_CSRF_ENABLED = False  # Disable CSRF for easier development


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    # Force HTTPS
    SESSION_COOKIE_SECURE = True

    # Stricter security
    BCRYPT_LOG_ROUNDS = 14

    # Enable all monitoring
    SQLALCHEMY_RECORD_QUERIES = True

    # Production email settings
    MAIL_SUPPRESS_SEND = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

    # Use PostgreSQL for tests (production-ready, matches MySQL behavior)
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'postgresql://postgres:postgres@localhost/opencats_test'

    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

    # Disable rate limiting
    RATELIMIT_ENABLED = False

    # Disable Redis session for tests (use filesystem)
    SESSION_TYPE = 'filesystem'

    # Faster password hashing for tests
    BCRYPT_LOG_ROUNDS = 4

    # Don't send emails in tests
    MAIL_SUPPRESS_SEND = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
