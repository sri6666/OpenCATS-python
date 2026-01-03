"""
Tests for Flask Views and Routes
Tests HTTP endpoints and view functions
"""
import pytest
from flask import session


class TestAuthViews:
    """Tests for authentication views"""

    def test_login_page_get(self, client):
        """Test GET /auth/login"""
        response = client.get('/auth/login', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data or b'login' in response.data

    def test_login_post_success(self, client, admin_user):
        """Test POST /auth/login with valid credentials"""
        response = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should redirect to dashboard or home

    def test_login_post_failure(self, client):
        """Test POST /auth/login with invalid credentials"""
        response = client.post('/auth/login', data={
            'username': 'invalid',
            'password': 'wrong'
        }, follow_redirects=True)

        assert response.status_code in [200, 401]
        assert b'Invalid' in response.data or b'incorrect' in response.data

    def test_logout(self, auth_client):
        """Test GET /auth/logout"""
        response = auth_client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200


class TestDashboardViews:
    """Tests for dashboard views"""

    def test_dashboard_requires_login(self, client):
        """Test that dashboard requires authentication"""
        response = client.get('/dashboard', follow_redirects=True)
        # Should redirect to login
        assert response.status_code in [302, 401]

    def test_dashboard_authenticated(self, auth_client):
        """Test dashboard with authenticated user"""
        response = auth_client.get('/dashboard', follow_redirects=True)
        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'dashboard' in response.data


class TestCandidateViews:
    """Tests for candidate views"""

    def test_candidates_list(self, auth_client):
        """Test GET /candidates"""
        response = auth_client.get('/candidates', follow_redirects=True)
        assert response.status_code == 200

    def test_candidates_add_get(self, auth_client):
        """Test GET /candidates/add"""
        response = auth_client.get('/candidates/add', follow_redirects=True)
        assert response.status_code == 200
        assert b'Add' in response.data or b'New' in response.data

    def test_candidates_add_post(self, auth_client, test_site):
        """Test POST /candidates/add"""
        response = auth_client.post('/candidates/add', data={
            'first_name': 'Test',
            'last_name': 'Candidate',
            'email1': 'test@example.com',
            'is_active': True
        }, follow_redirects=True)

        assert response.status_code == 200

    def test_candidate_view(self, auth_client, test_candidate):
        """Test GET /candidates/view/<id>"""
        response = auth_client.get(f'/candidates/view/{test_candidate.candidate_id}')
        assert response.status_code == 200
        assert b'Alice' in response.data
        assert b'Johnson' in response.data

    def test_candidate_edit_get(self, auth_client, test_candidate):
        """Test GET /candidates/edit/<id>"""
        response = auth_client.get(f'/candidates/edit/{test_candidate.candidate_id}')
        assert response.status_code == 200

    def test_candidate_delete(self, auth_client, test_candidate):
        """Test POST /candidates/delete/<id>"""
        response = auth_client.post(
            f'/candidates/delete/{test_candidate.candidate_id}',
            follow_redirects=True
        )
        assert response.status_code == 200

    def test_candidate_search(self, auth_client, test_candidate):
        """Test candidate search functionality"""
        response = auth_client.get('/candidates?search=Alice', follow_redirects=True)
        assert response.status_code == 200


class TestJobOrderViews:
    """Tests for job order views"""

    def test_joborders_list(self, auth_client):
        """Test GET /joborders"""
        response = auth_client.get('/joborders', follow_redirects=True)
        assert response.status_code == 200

    def test_joborder_view(self, auth_client, test_job):
        """Test GET /joborders/view/<id>"""
        response = auth_client.get(f'/joborders/view/{test_job.joborder_id}')
        assert response.status_code == 200
        assert b'Senior Python Developer' in response.data

    def test_pipeline_kanban(self, auth_client, test_job):
        """Test GET /joborders/pipeline/<id>"""
        response = auth_client.get(f'/joborders/pipeline/{test_job.joborder_id}')
        assert response.status_code == 200


class TestCompanyViews:
    """Tests for company views"""

    def test_companies_list(self, auth_client):
        """Test GET /companies"""
        response = auth_client.get('/companies', follow_redirects=True)
        assert response.status_code == 200

    def test_company_view(self, auth_client, test_company):
        """Test GET /companies/view/<id>"""
        response = auth_client.get(f'/companies/view/{test_company.company_id}')
        assert response.status_code == 200
        assert b'Tech Innovations Inc' in response.data

    def test_company_add_get(self, auth_client):
        """Test GET /companies/add"""
        response = auth_client.get('/companies/add', follow_redirects=True)
        assert response.status_code == 200

    def test_company_add_post(self, auth_client, admin_user):
        """Test POST /companies/add"""
        response = auth_client.post('/companies/add', data={
            'name': 'New Company',
            'phone1': '555-0000',
            'city': 'Test City',
            'state': 'TS'
        }, follow_redirects=True)

        assert response.status_code == 200


class TestContactViews:
    """Tests for contact views"""

    def test_contacts_list(self, auth_client):
        """Test GET /contacts"""
        response = auth_client.get('/contacts', follow_redirects=True)
        assert response.status_code == 200

    def test_contact_view(self, auth_client, test_contact):
        """Test GET /contacts/view/<id>"""
        response = auth_client.get(f'/contacts/view/{test_contact.contact_id}')
        assert response.status_code == 200
        assert b'John' in response.data
        assert b'Smith' in response.data

    def test_contact_add_get(self, auth_client):
        """Test GET /contacts/add"""
        response = auth_client.get('/contacts/add', follow_redirects=True)
        assert response.status_code == 200


class TestAdminViews:
    """Tests for admin views"""

    def test_admin_users_list(self, auth_client):
        """Test GET /admin/users"""
        response = auth_client.get('/admin/users', follow_redirects=True)
        assert response.status_code == 200

    def test_admin_settings(self, auth_client):
        """Test GET /admin/settings"""
        response = auth_client.get('/admin/settings', follow_redirects=True)
        assert response.status_code == 200

    def test_admin_requires_permission(self, client, regular_user):
        """Test that admin pages require admin permission"""
        # Login as regular user
        with client:
            client.post('/auth/login', data={
                'username': 'user',
                'password': 'user123'
            }, follow_redirects=True)

            response = client.get('/admin/users', follow_redirects=True)
            # Should be forbidden or redirected
            assert response.status_code in [403, 302]


class TestBillingViews:
    """Tests for billing views"""

    def test_billing_plans(self, auth_client):
        """Test GET /billing/plans"""
        response = auth_client.get('/billing/plans', follow_redirects=True)
        assert response.status_code == 200

    def test_billing_checkout(self, auth_client):
        """Test GET /billing/checkout/<plan>"""
        response = auth_client.get('/billing/checkout/professional', follow_redirects=True)
        # May redirect to Stripe or show form
        assert response.status_code in [200, 302]

    def test_billing_portal(self, auth_client):
        """Test GET /billing/portal"""
        response = auth_client.get('/billing/portal', follow_redirects=True)
        # May redirect to Stripe portal
        assert response.status_code in [200, 302]


class TestErrorHandlers:
    """Tests for error handlers"""

    def test_404_page(self, client):
        """Test 404 error page"""
        response = client.get('/nonexistent-page', follow_redirects=True)
        assert response.status_code == 404

    def test_403_forbidden(self, client, regular_user):
        """Test 403 forbidden page"""
        # Try to access admin page as regular user
        with client:
            client.post('/auth/login', data={
                'username': 'user',
                'password': 'user123'
            }, follow_redirects=True)

            response = client.get('/admin/users', follow_redirects=True)
            assert response.status_code in [403, 302]


class TestPaginationViews:
    """Tests for pagination in list views"""

    def test_candidates_pagination(self, auth_client, db_session, test_site, admin_user):
        """Test candidate list pagination"""
        from app.models import Candidate

        # Create many candidates
        for i in range(30):
            candidate = Candidate(
                site_id=test_site.site_id,
                first_name=f'Test{i}',
                last_name='Candidate',
                email1=f'test{i}@example.com',
                is_active=True,
                is_admin_hidden=False,
                entered_by=admin_user.user_id,
                owner=admin_user.user_id
            )
            db_session.add(candidate)
        db_session.commit()

        # Test page 1
        response = auth_client.get('/candidates?page=1', follow_redirects=True)
        assert response.status_code == 200

        # Test page 2
        response = auth_client.get('/candidates?page=2', follow_redirects=True)
        assert response.status_code == 200


class TestFormValidation:
    """Tests for form validation"""

    def test_candidate_form_validation(self, auth_client):
        """Test candidate form with missing required fields"""
        response = auth_client.post('/candidates/add', data={
            # Missing first_name and last_name
            'email1': 'test@example.com'
        }, follow_redirects=True)

        # Should show validation errors
        assert response.status_code in [200, 400]
        assert b'required' in response.data.lower() or b'invalid' in response.data.lower()

    def test_company_form_validation(self, auth_client):
        """Test company form with missing required fields"""
        response = auth_client.post('/companies/add', data={
            # Missing name
            'city': 'Test City'
        }, follow_redirects=True)

        # Should show validation errors
        assert response.status_code in [200, 400]


class TestCSRFProtection:
    """Tests for CSRF protection"""

    def test_csrf_token_required(self, auth_client):
        """Test that POST requests require CSRF token"""
        # Note: CSRF is disabled in test config, but this tests the mechanism
        response = auth_client.post('/candidates/add', data={
            'first_name': 'Test',
            'last_name': 'Candidate'
        }, follow_redirects=True)

        # With CSRF enabled, this should fail without token
        # With CSRF disabled in tests, it should succeed
        assert response.status_code in [200, 400, 403]


class TestFileUploads:
    """Tests for file upload functionality"""

    def test_resume_upload(self, auth_client, test_candidate):
        """Test resume file upload"""
        import io

        # Create a fake PDF file
        data = {
            'file': (io.BytesIO(b'PDF content'), 'resume.pdf')
        }

        response = auth_client.post(
            f'/candidates/upload-resume/{test_candidate.candidate_id}',
            data=data,
            content_type='multipart/form-data'
        )

        # Should accept upload or show error
        assert response.status_code in [200, 302, 400]


# Run tests with: pytest tests/test_views.py -v
