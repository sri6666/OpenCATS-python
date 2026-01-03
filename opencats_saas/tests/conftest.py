"""
Pytest Configuration and Fixtures
Provides common test fixtures for OpenCATS testing
"""
import pytest
import os
from datetime import datetime
from app import create_app
from app.extensions import db
from app.models import Site, User, Candidate, JobOrder, Company, Contact


@pytest.fixture(scope='session')
def app():
    """Create application instance for testing"""
    # Set environment variable to prevent loading .env
    os.environ['TESTING'] = '1'

    # Create app with testing config (uses PostgreSQL from config)
    app = create_app('testing')
    app.config['SERVER_NAME'] = 'localhost.localdomain'

    # Create all tables in test database
    with app.app_context():
        db.create_all()

    yield app

    # Drop all tables after test session (with CASCADE to handle circular dependencies)
    with app.app_context():
        db.session.remove()
        db.session.execute(db.text('DROP SCHEMA public CASCADE'))
        db.session.execute(db.text('CREATE SCHEMA public'))
        db.session.commit()


@pytest.fixture(scope='function')
def _db(app):
    """Provide clean database for each test"""
    with app.app_context():
        yield db

        # Clean up all tables after each test for isolation
        # Use TRUNCATE with CASCADE to handle foreign key constraints
        db.session.remove()
        # Quote table names to handle reserved keywords like 'user'
        table_names = ', '.join([f'"{table.name}"' for table in db.metadata.sorted_tables])
        if table_names:
            db.session.execute(db.text(f'TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE'))
            db.session.commit()


@pytest.fixture(scope='function')
def db_session(app, _db):
    """Create a new database session for each test"""
    with app.app_context():
        yield _db.session


@pytest.fixture
def client(app, db_session):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


# ============================================================================
# Data Fixtures
# ============================================================================

@pytest.fixture
def test_site(db_session):
    """Create a test site"""
    site = Site(
        name='Test Company',
        subdomain='testcompany',
        subscription_plan='professional',
        subscription_status='active',
        is_active=True
    )
    db_session.add(site)
    db_session.commit()
    return site


@pytest.fixture
def admin_user(db_session, test_site):
    """Create an admin user"""
    user = User(
        site_id=test_site.site_id,
        username='admin',
        email='admin@test.com',
        first_name='Admin',
        last_name='User',
        access_level=500,  # Root
        is_active=True
    )
    user.set_password('admin123')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def regular_user(db_session, test_site):
    """Create a regular user"""
    user = User(
        site_id=test_site.site_id,
        username='user',
        email='user@test.com',
        first_name='Regular',
        last_name='User',
        access_level=200,  # Edit
        is_active=True
    )
    user.set_password('user123')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_company(db_session, test_site, admin_user):
    """Create a test company"""
    company = Company(
        site_id=test_site.site_id,
        name='Tech Innovations Inc',
        phone1='555-0100',
        city='San Francisco',
        state='CA',
        is_admin_hidden=False,
        entered_by=admin_user.user_id
    )
    db_session.add(company)
    db_session.commit()
    return company


@pytest.fixture
def test_contact(db_session, test_site, test_company, admin_user):
    """Create a test contact"""
    contact = Contact(
        site_id=test_site.site_id,
        company_id=test_company.company_id,
        first_name='John',
        last_name='Smith',
        title='HR Manager',
        email1='john.smith@techinnovations.com',
        phone_work='555-0101',
        is_admin_hidden=False,
        entered_by=admin_user.user_id
    )
    db_session.add(contact)
    db_session.commit()
    return contact


@pytest.fixture
def test_candidate(db_session, test_site, admin_user):
    """Create a test candidate"""
    candidate = Candidate(
        site_id=test_site.site_id,
        first_name='Alice',
        last_name='Johnson',
        email1='alice.johnson@email.com',
        phone_cell='555-0201',
        key_skills='Python, Flask, SQLAlchemy, PostgreSQL',
        current_employer='Tech Corp',
        is_hot=True,
        is_active=True,
        is_admin_hidden=False,
        entered_by=admin_user.user_id,
        owner=admin_user.user_id
    )
    db_session.add(candidate)
    db_session.commit()
    return candidate


@pytest.fixture
def test_job(db_session, test_site, test_company, test_contact, admin_user):
    """Create a test job order"""
    job = JobOrder(
        site_id=test_site.site_id,
        recruiter=admin_user.user_id,
        company_id=test_company.company_id,
        contact_id=test_contact.contact_id,
        title='Senior Python Developer',
        description='We are looking for an experienced Python developer...',
        type='H',  # Full-time
        duration='Permanent',
        rate_max='150000',
        salary='120000-150000',
        status=0,  # Active
        openings=2,
        openings_available=2,
        city='San Francisco',
        state='CA',
        is_admin_hidden=False,
        entered_by=admin_user.user_id
    )
    db_session.add(job)
    db_session.commit()
    return job


@pytest.fixture
def auth_client(client, admin_user):
    """Create an authenticated client"""
    with client.session_transaction() as session:
        session['user_id'] = admin_user.user_id
        session['_fresh'] = True
    return client


@pytest.fixture
def api_headers(test_site):
    """Create API authentication headers"""
    return {
        'X-API-Key': test_site.api_key,
        'Content-Type': 'application/json'
    }


# ============================================================================
# Helper Functions
# ============================================================================

def login_user(client, username='admin', password='admin123'):
    """Helper function to log in a user"""
    return client.post('/auth/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)


def logout_user(client):
    """Helper function to log out"""
    return client.get('/auth/logout', follow_redirects=True)


def create_candidate(db_session, site_id, user_id, **kwargs):
    """Helper function to create a candidate"""
    defaults = {
        'site_id': site_id,
        'first_name': 'Test',
        'last_name': 'Candidate',
        'email1': 'test@example.com',
        'is_active': True,
        'is_admin_hidden': False,
        'entered_by': user_id,
        'owner': user_id
    }
    defaults.update(kwargs)

    candidate = Candidate(**defaults)
    db_session.add(candidate)
    db_session.commit()
    return candidate


def create_job(db_session, site_id, company_id, user_id, **kwargs):
    """Helper function to create a job order"""
    defaults = {
        'site_id': site_id,
        'company_id': company_id,
        'recruiter': user_id,
        'title': 'Test Job',
        'type': 'H',
        'status': 0,
        'openings': 1,
        'openings_available': 1,
        'is_admin_hidden': False,
        'entered_by': user_id
    }
    defaults.update(kwargs)

    job = JobOrder(**defaults)
    db_session.add(job)
    db_session.commit()
    return job
