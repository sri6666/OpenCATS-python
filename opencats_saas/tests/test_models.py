"""
Unit Tests for Database Models
Tests all model classes and their methods
"""
import pytest
from datetime import datetime
from app.models import Site, User, Candidate, JobOrder, Company, Contact, CandidateJobOrder
from app.extensions import db


class TestSiteModel:
    """Tests for Site model"""

    def test_create_site(self, db_session):
        """Test creating a new site"""
        site = Site(
            name='Test Site',
            subdomain='testsite',
            subscription_plan='starter',
            subscription_status='trial',
            is_active=True
        )
        db_session.add(site)
        db_session.commit()

        assert site.site_id is not None
        assert site.name == 'Test Site'
        assert site.subdomain == 'testsite'
        assert site.is_active is True

    def test_site_can_add_user(self, test_site):
        """Test site user limit checks"""
        # Professional plan should allow multiple users
        assert test_site.can_add_user() is True

    def test_site_storage_limit(self, test_site):
        """Test storage limit calculation"""
        # Professional plan should have storage limit
        assert test_site.storage_limit_mb > 0

    def test_site_repr(self, test_site):
        """Test site string representation"""
        assert 'Test Company' in repr(test_site)
        assert 'testcompany' in repr(test_site)


class TestUserModel:
    """Tests for User model"""

    def test_create_user(self, db_session, test_site):
        """Test creating a new user"""
        user = User(
            site_id=test_site.site_id,
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            access_level=200,
            is_active=True
        )
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()

        assert user.user_id is not None
        assert user.username == 'testuser'
        assert user.password_hash is not None

    def test_password_hashing(self, admin_user):
        """Test password hashing and verification"""
        admin_user.set_password('newpassword')
        assert admin_user.check_password('newpassword') is True
        assert admin_user.check_password('wrongpassword') is False

    def test_full_name_property(self, admin_user):
        """Test full_name property"""
        assert admin_user.full_name == 'Admin User'

        # Test with user without names
        admin_user.first_name = None
        admin_user.last_name = None
        assert admin_user.full_name == 'admin'

    def test_is_admin_property(self, admin_user, regular_user):
        """Test is_admin property"""
        assert admin_user.is_admin is True
        assert regular_user.is_admin is False

    def test_is_root_property(self, admin_user, regular_user):
        """Test is_root property"""
        assert admin_user.is_root is True
        assert regular_user.is_root is False

    def test_has_permission(self, admin_user, regular_user):
        """Test permission checking"""
        # Admin should have all permissions
        assert admin_user.has_permission('edit') is True
        assert admin_user.has_permission('delete') is True

    def test_user_repr(self, admin_user):
        """Test user string representation"""
        assert 'admin' in repr(admin_user)


class TestCandidateModel:
    """Tests for Candidate model"""

    def test_create_candidate(self, db_session, test_site, admin_user):
        """Test creating a new candidate"""
        candidate = Candidate(
            site_id=test_site.site_id,
            first_name='John',
            last_name='Doe',
            email1='john.doe@example.com',
            phone_cell='555-1234',
            key_skills='Python, JavaScript',
            is_active=True,
            is_admin_hidden=False,
            entered_by=admin_user.user_id,
            owner=admin_user.user_id
        )
        db_session.add(candidate)
        db_session.commit()

        assert candidate.candidate_id is not None
        assert candidate.first_name == 'John'
        assert candidate.last_name == 'Doe'

    def test_query_for_site(self, test_site, test_candidate, db_session):
        """Test site-specific candidate querying"""
        # Create another site and candidate
        other_site = Site(
            name='Other Site',
            subdomain='othersite',
            subscription_plan='starter',
            is_active=True
        )
        db_session.add(other_site)
        db_session.commit()

        other_candidate = Candidate(
            site_id=other_site.site_id,
            first_name='Other',
            last_name='Candidate',
            email1='other@example.com',
            is_active=True,
            is_admin_hidden=False
        )
        db_session.add(other_candidate)
        db_session.commit()

        # Query should only return candidates for test_site
        candidates = Candidate.query_for_site(test_site.site_id).all()
        assert len(candidates) == 1
        assert candidates[0].candidate_id == test_candidate.candidate_id

    def test_candidate_full_name(self, test_candidate):
        """Test candidate full name"""
        assert test_candidate.first_name == 'Alice'
        assert test_candidate.last_name == 'Johnson'

    def test_candidate_hot_flag(self, test_candidate):
        """Test hot candidate flag"""
        assert test_candidate.is_hot is True


class TestJobOrderModel:
    """Tests for JobOrder model"""

    def test_create_job_order(self, db_session, test_site, test_company, admin_user):
        """Test creating a new job order"""
        job = JobOrder(
            site_id=test_site.site_id,
            recruiter=admin_user.user_id,
            company_id=test_company.company_id,
            title='Software Engineer',
            type=1,
            status=0,
            openings=3,
            openings_available=3,
            is_admin_hidden=False,
            entered_by=admin_user.user_id
        )
        db_session.add(job)
        db_session.commit()

        assert job.joborder_id is not None
        assert job.title == 'Software Engineer'
        assert job.openings == 3

    def test_query_for_site(self, test_site, test_job, db_session):
        """Test site-specific job querying"""
        # Create another site and job
        other_site = Site(
            name='Other Site',
            subdomain='othersite2',
            subscription_plan='starter',
            is_active=True
        )
        db_session.add(other_site)
        db_session.commit()

        other_job = JobOrder(
            site_id=other_site.site_id,
            title='Other Job',
            type=1,
            status=0,
            openings=1,
            is_admin_hidden=False
        )
        db_session.add(other_job)
        db_session.commit()

        # Query should only return jobs for test_site
        jobs = JobOrder.query_for_site(test_site.site_id).all()
        assert len(jobs) == 1
        assert jobs[0].joborder_id == test_job.joborder_id

    def test_job_active_status(self, test_job):
        """Test job active status"""
        assert test_job.status == 0  # Active
        test_job.status = 1  # Inactive
        assert test_job.status == 1


class TestCompanyModel:
    """Tests for Company model"""

    def test_create_company(self, db_session, test_site, admin_user):
        """Test creating a new company"""
        company = Company(
            site_id=test_site.site_id,
            name='Acme Corp',
            phone1='555-1000',
            city='New York',
            state='NY',
            is_admin_hidden=False,
            entered_by=admin_user.user_id
        )
        db_session.add(company)
        db_session.commit()

        assert company.company_id is not None
        assert company.name == 'Acme Corp'
        assert company.city == 'New York'

    def test_company_relationships(self, test_company, test_contact, test_job):
        """Test company relationships"""
        # Company should have contacts and jobs
        assert test_contact in test_company.contacts
        assert test_job in test_company.joborders


class TestContactModel:
    """Tests for Contact model"""

    def test_create_contact(self, db_session, test_site, test_company, admin_user):
        """Test creating a new contact"""
        contact = Contact(
            site_id=test_site.site_id,
            company_id=test_company.company_id,
            first_name='Jane',
            last_name='Doe',
            title='Recruiter',
            email1='jane.doe@company.com',
            phone_work='555-2000',
            entered_by=admin_user.user_id
        )
        db_session.add(contact)
        db_session.commit()

        assert contact.contact_id is not None
        assert contact.first_name == 'Jane'
        assert contact.email1 == 'jane.doe@company.com'

    def test_contact_company_relationship(self, test_contact, test_company):
        """Test contact-company relationship"""
        assert test_contact.company_id == test_company.company_id
        assert test_contact.company == test_company


class TestCandidateJobOrderModel:
    """Tests for CandidateJobOrder (pipeline) model"""

    def test_add_candidate_to_job(self, db_session, test_site, test_candidate, test_job, admin_user):
        """Test adding a candidate to a job pipeline"""
        pipeline = CandidateJobOrder(
            site_id=test_site.site_id,
            candidate_id=test_candidate.candidate_id,
            joborder_id=test_job.joborder_id,
            status=200,  # Contacted
            added_by=admin_user.user_id
        )
        db_session.add(pipeline)
        db_session.commit()

        assert pipeline.candidatejoborder_id is not None
        assert pipeline.status == 200
        assert pipeline.candidate_id == test_candidate.candidate_id

    def test_pipeline_status_updates(self, db_session, test_site, test_candidate, test_job, admin_user):
        """Test updating pipeline status"""
        pipeline = CandidateJobOrder(
            site_id=test_site.site_id,
            candidate_id=test_candidate.candidate_id,
            joborder_id=test_job.joborder_id,
            status=0,  # No Contact
            added_by=admin_user.user_id
        )
        db_session.add(pipeline)
        db_session.commit()

        # Update status to Interviewed
        pipeline.status = 600
        db_session.commit()

        assert pipeline.status == 600


class TestModelTimestamps:
    """Tests for automatic timestamps"""

    def test_date_created(self, test_candidate):
        """Test date_created is set automatically"""
        assert test_candidate.date_created is not None
        assert isinstance(test_candidate.date_created, datetime)

    def test_date_modified(self, test_candidate, db_session):
        """Test date_modified is updated on changes"""
        original_modified = test_candidate.date_modified

        # Update candidate
        test_candidate.is_hot = False
        db_session.commit()

        # date_modified should be updated (or at least not earlier)
        assert test_candidate.date_modified >= original_modified


class TestModelValidation:
    """Tests for model validation"""

    def test_candidate_requires_name(self, db_session, test_site):
        """Test that candidate requires first and last name"""
        with pytest.raises(Exception):  # Should raise IntegrityError
            candidate = Candidate(
                site_id=test_site.site_id,
                # Missing first_name and last_name
                email1='test@example.com'
            )
            db_session.add(candidate)
            db_session.commit()

    def test_user_requires_username(self, db_session, test_site):
        """Test that user requires username"""
        with pytest.raises(Exception):  # Should raise IntegrityError
            user = User(
                site_id=test_site.site_id,
                # Missing username
                email='test@example.com',
                access_level=100
            )
            db_session.add(user)
            db_session.commit()


# Run tests with: pytest tests/test_models.py -v
