"""
Integration Tests for API Endpoints
Tests REST API functionality with full coverage
"""
import pytest
import json
from app.models import Candidate, JobOrder, Company, Contact


class TestAPIAuth:
    """Tests for API authentication"""

    def test_api_requires_auth(self, client):
        """Test that API requires authentication"""
        response = client.get('/api/v1/candidates')
        assert response.status_code == 401

    def test_api_with_invalid_key(self, client):
        """Test API with invalid key"""
        headers = {'X-API-Key': 'invalid-key'}
        response = client.get('/api/v1/candidates', headers=headers)
        assert response.status_code == 401

    def test_api_with_valid_key(self, client, test_site, api_headers):
        """Test API with valid key"""
        # First generate API key for site
        test_site.api_key = 'test-api-key-123'

        headers = {'X-API-Key': 'test-api-key-123'}
        response = client.get('/api/v1/candidates', headers=headers)
        assert response.status_code in [200, 404]  # May not have candidates yet


class TestCandidateAPI:
    """Tests for Candidate API endpoints"""

    def test_list_candidates(self, client, test_site, test_candidate, api_headers):
        """Test GET /api/v1/candidates"""
        test_site.api_key = 'test-key'
        headers = {'X-API-Key': 'test-key'}

        response = client.get('/api/v1/candidates', headers=headers)
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'candidates' in data or isinstance(data, list)

    def test_get_candidate_detail(self, client, test_site, test_candidate, api_headers):
        """Test GET /api/v1/candidates/<id>"""
        test_site.api_key = 'test-key'
        headers = {'X-API-Key': 'test-key'}

        response = client.get(
            f'/api/v1/candidates/{test_candidate.candidate_id}',
            headers=headers
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['first_name'] == 'Alice'
        assert data['last_name'] == 'Johnson'

    def test_create_candidate(self, client, test_site, admin_user):
        """Test POST /api/v1/candidates"""
        test_site.api_key = 'test-key'
        headers = {
            'X-API-Key': 'test-key',
            'Content-Type': 'application/json'
        }

        candidate_data = {
            'first_name': 'Bob',
            'last_name': 'Smith',
            'email1': 'bob.smith@example.com',
            'phone_cell': '555-3333',
            'key_skills': 'Java, Spring, MySQL'
        }

        response = client.post(
            '/api/v1/candidates',
            headers=headers,
            data=json.dumps(candidate_data)
        )
        assert response.status_code in [201, 200]

        data = json.loads(response.data)
        assert data['first_name'] == 'Bob'
        assert 'candidate_id' in data

    def test_update_candidate(self, client, test_site, test_candidate):
        """Test PUT /api/v1/candidates/<id>"""
        test_site.api_key = 'test-key'
        headers = {
            'X-API-Key': 'test-key',
            'Content-Type': 'application/json'
        }

        update_data = {
            'is_hot': False,
            'key_skills': 'Python, Django, React'
        }

        response = client.put(
            f'/api/v1/candidates/{test_candidate.candidate_id}',
            headers=headers,
            data=json.dumps(update_data)
        )
        assert response.status_code in [200, 204]

    def test_delete_candidate(self, client, test_site, test_candidate):
        """Test DELETE /api/v1/candidates/<id>"""
        test_site.api_key = 'test-key'
        headers = {'X-API-Key': 'test-key'}

        response = client.delete(
            f'/api/v1/candidates/{test_candidate.candidate_id}',
            headers=headers
        )
        assert response.status_code in [200, 204]

    def test_search_candidates(self, client, test_site, test_candidate):
        """Test GET /api/v1/candidates?search=keyword"""
        test_site.api_key = 'test-key'
        headers = {'X-API-Key': 'test-key'}

        response = client.get(
            '/api/v1/candidates?search=Alice',
            headers=headers
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        if isinstance(data, dict) and 'candidates' in data:
            candidates = data['candidates']
        else:
            candidates = data

        # Should find Alice Johnson
        assert any(c['first_name'] == 'Alice' for c in candidates)


class TestJobOrderAPI:
    """Tests for JobOrder API endpoints"""

    def test_list_jobs(self, client, test_site, test_job):
        """Test GET /api/v1/joborders"""
        test_site.api_key = 'test-key'
        headers = {'X-API-Key': 'test-key'}

        response = client.get('/api/v1/joborders', headers=headers)
        assert response.status_code == 200

    def test_get_job_detail(self, client, test_site, test_job):
        """Test GET /api/v1/joborders/<id>"""
        test_site.api_key = 'test-key'
        headers = {'X-API-Key': 'test-key'}

        response = client.get(
            f'/api/v1/joborders/{test_job.joborder_id}',
            headers=headers
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['title'] == 'Senior Python Developer'

    def test_create_job(self, client, test_site, test_company, admin_user):
        """Test POST /api/v1/joborders"""
        test_site.api_key = 'test-key'
        headers = {
            'X-API-Key': 'test-key',
            'Content-Type': 'application/json'
        }

        job_data = {
            'title': 'Full Stack Developer',
            'company_id': test_company.company_id,
            'type': 'H',
            'status': 0,
            'openings': 2,
            'city': 'New York',
            'state': 'NY'
        }

        response = client.post(
            '/api/v1/joborders',
            headers=headers,
            data=json.dumps(job_data)
        )
        assert response.status_code in [201, 200]


class TestCompanyAPI:
    """Tests for Company API endpoints"""

    def test_list_companies(self, client, test_site, test_company):
        """Test GET /api/v1/companies"""
        test_site.api_key = 'test-key'
        headers = {'X-API-Key': 'test-key'}

        response = client.get('/api/v1/companies', headers=headers)
        assert response.status_code == 200

    def test_get_company_detail(self, client, test_site, test_company):
        """Test GET /api/v1/companies/<id>"""
        test_site.api_key = 'test-key'
        headers = {'X-API-Key': 'test-key'}

        response = client.get(
            f'/api/v1/companies/{test_company.company_id}',
            headers=headers
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['name'] == 'Tech Innovations Inc'

    def test_create_company(self, client, test_site, admin_user):
        """Test POST /api/v1/companies"""
        test_site.api_key = 'test-key'
        headers = {
            'X-API-Key': 'test-key',
            'Content-Type': 'application/json'
        }

        company_data = {
            'name': 'New Tech Corp',
            'phone1': '555-9999',
            'city': 'Boston',
            'state': 'MA'
        }

        response = client.post(
            '/api/v1/companies',
            headers=headers,
            data=json.dumps(company_data)
        )
        assert response.status_code in [201, 200]


class TestContactAPI:
    """Tests for Contact API endpoints"""

    def test_list_contacts(self, client, test_site, test_contact):
        """Test GET /api/v1/contacts"""
        test_site.api_key = 'test-key'
        headers = {'X-API-Key': 'test-key'}

        response = client.get('/api/v1/contacts', headers=headers)
        assert response.status_code == 200

    def test_get_contact_detail(self, client, test_site, test_contact):
        """Test GET /api/v1/contacts/<id>"""
        test_site.api_key = 'test-key'
        headers = {'X-API-Key': 'test-key'}

        response = client.get(
            f'/api/v1/contacts/{test_contact.contact_id}',
            headers=headers
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['first_name'] == 'John'
        assert data['last_name'] == 'Smith'


class TestPipelineAPI:
    """Tests for candidate pipeline API"""

    def test_add_candidate_to_job(self, client, test_site, test_candidate, test_job):
        """Test POST /api/v1/pipeline"""
        test_site.api_key = 'test-key'
        headers = {
            'X-API-Key': 'test-key',
            'Content-Type': 'application/json'
        }

        pipeline_data = {
            'candidate_id': test_candidate.candidate_id,
            'joborder_id': test_job.joborder_id,
            'status': 200  # Contacted
        }

        response = client.post(
            '/api/v1/pipeline',
            headers=headers,
            data=json.dumps(pipeline_data)
        )
        assert response.status_code in [201, 200]

    def test_update_pipeline_status(self, client, test_site, test_candidate, test_job, db_session):
        """Test PUT /api/v1/pipeline/<id>"""
        from app.models import CandidateJobOrder

        # Create pipeline entry
        pipeline = CandidateJobOrder(
            site_id=test_site.site_id,
            candidate_id=test_candidate.candidate_id,
            joborder_id=test_job.joborder_id,
            status=200,
            added_by=1
        )
        db_session.add(pipeline)
        db_session.commit()

        test_site.api_key = 'test-key'
        headers = {
            'X-API-Key': 'test-key',
            'Content-Type': 'application/json'
        }

        update_data = {'status': 600}  # Interviewed

        response = client.put(
            f'/api/v1/pipeline/{pipeline.candidatejoborder_id}',
            headers=headers,
            data=json.dumps(update_data)
        )
        assert response.status_code in [200, 204]


class TestAPIFiltering:
    """Tests for API filtering and pagination"""

    def test_filter_by_status(self, client, test_site, test_candidate):
        """Test filtering candidates by status"""
        test_site.api_key = 'test-key'
        headers = {'X-API-Key': 'test-key'}

        response = client.get(
            '/api/v1/candidates?is_active=true',
            headers=headers
        )
        assert response.status_code == 200

    def test_pagination(self, client, test_site, db_session, admin_user):
        """Test API pagination"""
        # Create multiple candidates
        for i in range(25):
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

        test_site.api_key = 'test-key'
        headers = {'X-API-Key': 'test-key'}

        # Request first page
        response = client.get(
            '/api/v1/candidates?page=1&per_page=10',
            headers=headers
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        # Should return pagination info
        assert 'total' in data or 'count' in data or isinstance(data, list)

    def test_sorting(self, client, test_site, test_candidate):
        """Test API sorting"""
        test_site.api_key = 'test-key'
        headers = {'X-API-Key': 'test-key'}

        response = client.get(
            '/api/v1/candidates?sort=last_name&order=asc',
            headers=headers
        )
        assert response.status_code == 200


class TestAPIErrors:
    """Tests for API error handling"""

    def test_404_not_found(self, client, test_site):
        """Test 404 error for non-existent resource"""
        test_site.api_key = 'test-key'
        headers = {'X-API-Key': 'test-key'}

        response = client.get('/api/v1/candidates/99999', headers=headers)
        assert response.status_code == 404

    def test_400_bad_request(self, client, test_site):
        """Test 400 error for invalid data"""
        test_site.api_key = 'test-key'
        headers = {
            'X-API-Key': 'test-key',
            'Content-Type': 'application/json'
        }

        # Missing required fields
        invalid_data = {}

        response = client.post(
            '/api/v1/candidates',
            headers=headers,
            data=json.dumps(invalid_data)
        )
        assert response.status_code in [400, 422]

    def test_method_not_allowed(self, client, test_site):
        """Test 405 error for unsupported method"""
        test_site.api_key = 'test-key'
        headers = {'X-API-Key': 'test-key'}

        # PATCH might not be supported
        response = client.patch('/api/v1/candidates/1', headers=headers)
        assert response.status_code in [405, 501]


# Run tests with: pytest tests/test_api.py -v
