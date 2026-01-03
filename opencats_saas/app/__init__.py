"""
Application Factory for OpenCATS SaaS
"""
import os
from flask import Flask
from config import config


def create_app(config_name=None):
    """
    Application factory pattern

    Args:
        config_name: Configuration to use (development, production, testing)

    Returns:
        Flask application instance
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    from app.extensions import (
        db, migrate, login_manager, mail, csrf, limiter,
        cache, celery_app
    )

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)

    # Initialize Celery
    celery_app.conf.update(app.config)

    # Register blueprints
    from app.auth import auth_bp
    from app.candidates import candidates_bp
    from app.joborders import joborders_bp
    from app.companies import companies_bp
    from app.contacts import contacts_bp
    from app.api import api_bp
    from app.main import main_bp
    from app.admin import admin_bp
    from app.billing import billing_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(candidates_bp, url_prefix='/candidates')
    app.register_blueprint(joborders_bp, url_prefix='/joborders')
    app.register_blueprint(companies_bp, url_prefix='/companies')
    app.register_blueprint(contacts_bp, url_prefix='/contacts')
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(billing_bp, url_prefix='/billing')

    # Register error handlers
    register_error_handlers(app)

    # Register template filters
    register_template_filters(app)

    # Register CLI commands
    register_cli_commands(app)

    # Initialize Sentry for error tracking
    if app.config.get('SENTRY_DSN'):
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration

        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.1,
            environment=config_name
        )

    return app


def register_error_handlers(app):
    """Register error handlers"""
    from flask import render_template, jsonify, request

    @app.errorhandler(403)
    def forbidden(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden'}), 403
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not found'}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500


def register_template_filters(app):
    """Register custom Jinja2 filters"""
    from datetime import datetime

    @app.template_filter('datetime')
    def format_datetime(value, format='%Y-%m-%d %H:%M'):
        if value is None:
            return ''
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        return value.strftime(format)

    @app.template_filter('date')
    def format_date(value):
        return format_datetime(value, '%Y-%m-%d')

    @app.template_filter('timeago')
    def timeago(value):
        if value is None:
            return ''
        from datetime import datetime
        now = datetime.utcnow()
        diff = now - value

        if diff.days > 365:
            return f'{diff.days // 365} years ago'
        elif diff.days > 30:
            return f'{diff.days // 30} months ago'
        elif diff.days > 0:
            return f'{diff.days} days ago'
        elif diff.seconds > 3600:
            return f'{diff.seconds // 3600} hours ago'
        elif diff.seconds > 60:
            return f'{diff.seconds // 60} minutes ago'
        else:
            return 'just now'


def register_cli_commands(app):
    """Register CLI commands"""
    from app.extensions import db

    @app.cli.command()
    def init_db():
        """Initialize the database"""
        db.create_all()
        print('Database initialized.')

    @app.cli.command()
    def seed_db():
        """Seed the database with sample data"""
        from app.models import Site, User
        from werkzeug.security import generate_password_hash

        # Create default site
        site = Site(
            name='Demo Company',
            subdomain='demo',
            is_active=True
        )
        db.session.add(site)
        db.session.commit()

        # Create admin user
        admin = User(
            site_id=site.site_id,
            username='admin',
            email='admin@demo.com',
            first_name='Admin',
            last_name='User',
            access_level=500,
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

        print(f'Database seeded. Admin user: admin / admin123')

    @app.cli.command()
    def create_indexes():
        """Create Elasticsearch indexes"""
        from app.utils.search import SearchService
        search = SearchService()
        search.create_indexes()
        print('Elasticsearch indexes created.')
