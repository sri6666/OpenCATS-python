"""Pytest configuration for e2e tests"""
import os
import sys
import pytest
import time
import multiprocessing
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app import create_app
from app.models import db, User, Site
from playwright.sync_api import Page, Browser, BrowserContext

# Import playwright config
config_path = Path(__file__).parent.parent.parent / 'playwright.config'
sys.path.insert(0, str(config_path.parent))
import playwright_config as pw_config


@pytest.fixture(scope='session')
def flask_app():
    """Create and configure a Flask app instance for testing"""
    app = create_app('testing')

    with app.app_context():
        # Create all tables
        db.create_all()

        # Create test site
        site = Site.query.filter_by(subdomain='test').first()
        if not site:
            site = Site(
                name='Test Company',
                subdomain='test',
                is_active=True
            )
            db.session.add(site)
            db.session.commit()

        # Create test user with admin access
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            test_user = User(
                site_id=site.site_id,
                username='testuser',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                access_level=500,  # Root/admin access
                is_active=True
            )
            test_user.set_password('password123')
            db.session.add(test_user)
            db.session.commit()

    yield app

    # Cleanup - use same approach as unit tests to handle circular dependencies
    with app.app_context():
        db.session.remove()
        db.session.execute(db.text('DROP SCHEMA public CASCADE'))
        db.session.execute(db.text('CREATE SCHEMA public'))
        db.session.commit()


def run_flask_app(app):
    """Run Flask app in a separate process"""
    with app.app_context():
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)


@pytest.fixture(scope='session')
def live_server(flask_app):
    """Start Flask development server in background"""
    process = multiprocessing.Process(target=run_flask_app, args=(flask_app,))
    process.start()

    # Wait for server to start
    time.sleep(2)

    yield 'http://127.0.0.1:5000'

    # Cleanup
    process.terminate()
    process.join(timeout=5)
    if process.is_alive():
        process.kill()


@pytest.fixture(scope='session')
def browser_context_args(browser_context_args):
    """Configure browser context"""
    return {
        **browser_context_args,
        'viewport': pw_config.VIEWPORT,
        'ignore_https_errors': True,
    }


@pytest.fixture
def context(browser: Browser, browser_context_args):
    """Create a new browser context for each test"""
    context = browser.new_context(**browser_context_args)
    yield context
    context.close()


@pytest.fixture
def page(context: BrowserContext, live_server):
    """Create a new page for each test"""
    page = context.new_page()
    page.set_default_timeout(pw_config.TIMEOUT)
    page.set_default_navigation_timeout(pw_config.NAVIGATION_TIMEOUT)
    yield page
    page.close()


@pytest.fixture
def authenticated_page(page: Page, live_server):
    """Create an authenticated page by logging in"""
    # Navigate to login page
    page.goto(f'{live_server}/auth/login')

    # Fill in login form
    page.fill('input[name="email"]', 'test@example.com')
    page.fill('input[name="password"]', 'password123')

    # Submit form
    page.click('button[type="submit"]')

    # Wait for redirect to dashboard
    page.wait_for_url(f'{live_server}/dashboard', timeout=5000)

    yield page


class E2EHelpers:
    """Helper methods for e2e tests"""

    @staticmethod
    def login(page: Page, base_url: str, email: str = 'test@example.com', password: str = 'password123'):
        """Log in to the application"""
        page.goto(f'{base_url}/auth/login')
        page.fill('input[name="email"]', email)
        page.fill('input[name="password"]', password)
        page.click('button[type="submit"]')
        page.wait_for_url(f'{base_url}/dashboard')

    @staticmethod
    def logout(page: Page, base_url: str):
        """Log out from the application"""
        page.goto(f'{base_url}/auth/logout')
        page.wait_for_url(f'{base_url}/auth/login')

    @staticmethod
    def navigate_to(page: Page, base_url: str, path: str):
        """Navigate to a specific path"""
        page.goto(f'{base_url}{path}')
        page.wait_for_load_state('networkidle')


@pytest.fixture
def helpers():
    """Provide helper methods to tests"""
    return E2EHelpers()
