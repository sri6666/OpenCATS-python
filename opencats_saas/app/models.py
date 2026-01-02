"""
Database Models for OpenCATS SaaS

Multi-tenant architecture:
- Every entity belongs to a Site (tenant)
- Query filters automatically applied based on current user's site
"""
from datetime import datetime
from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from sqlalchemy.orm import Query
from app.extensions import db


# ============================================================================
# Base Models
# ============================================================================

class TenantQuery(Query):
    """Custom query class that automatically filters by tenant"""

    def __new__(cls, *args, **kwargs):
        if args and hasattr(args[0], '__bases__'):
            # Check if model has site_id
            if hasattr(args[0], 'site_id'):
                return Query(*args, **kwargs).filter_by(site_id=current_user.site_id if current_user.is_authenticated else None)
        return Query(*args, **kwargs)


class BaseModel(db.Model):
    """Base model with common fields"""
    __abstract__ = True

    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    date_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def save(self):
        """Save instance to database"""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Delete instance from database"""
        db.session.delete(self)
        db.session.commit()

    def to_dict(self):
        """Convert model to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TenantModel(BaseModel):
    """Base model for multi-tenant entities"""
    __abstract__ = True

    site_id = db.Column(db.Integer, db.ForeignKey('site.site_id'), nullable=False, index=True)
    entered_by = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    owner = db.Column(db.Integer, db.ForeignKey('user.user_id'))

    @classmethod
    def query_for_site(cls, site_id):
        """Query filtered by site"""
        return cls.query.filter_by(site_id=site_id)


# ============================================================================
# Site (Tenant) Model
# ============================================================================

class Site(BaseModel):
    """
    Site/Tenant model - represents a customer organization
    Each site is completely isolated from others
    """
    __tablename__ = 'site'

    site_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    subdomain = db.Column(db.String(64), unique=True, nullable=False, index=True)
    custom_domain = db.Column(db.String(255), unique=True, nullable=True)

    # Subscription
    subscription_plan = db.Column(db.String(50), default='starter')  # starter, professional, enterprise
    subscription_status = db.Column(db.String(50), default='trial')  # trial, active, past_due, canceled
    stripe_customer_id = db.Column(db.String(255), unique=True)
    stripe_subscription_id = db.Column(db.String(255), unique=True)
    trial_ends_at = db.Column(db.DateTime)
    subscription_ends_at = db.Column(db.DateTime)

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    # Settings
    logo_url = db.Column(db.String(500))
    timezone = db.Column(db.String(50), default='UTC')
    date_format = db.Column(db.String(20), default='%Y-%m-%d')

    # Usage tracking
    storage_used_mb = db.Column(db.Integer, default=0)

    # Relationships
    users = db.relationship('User', backref='site', lazy='dynamic')
    candidates = db.relationship('Candidate', backref='site', lazy='dynamic')
    companies = db.relationship('Company', backref='site', lazy='dynamic')
    joborders = db.relationship('JobOrder', backref='site', lazy='dynamic')

    def __repr__(self):
        return f'<Site {self.name} ({self.subdomain})>'

    def can_add_user(self):
        """Check if site can add more users based on plan"""
        from config import Config
        max_users = Config.SUBSCRIPTION_PLANS[self.subscription_plan]['features']['max_users']
        if max_users == -1:  # unlimited
            return True
        return self.users.count() < max_users

    def can_add_candidate(self):
        """Check if site can add more candidates"""
        from config import Config
        max_candidates = Config.SUBSCRIPTION_PLANS[self.subscription_plan]['features']['max_candidates']
        if max_candidates == -1:
            return True
        return self.candidates.count() < max_candidates

    def can_add_job(self):
        """Check if site can add more job orders"""
        from config import Config
        max_jobs = Config.SUBSCRIPTION_PLANS[self.subscription_plan]['features']['max_jobs']
        if max_jobs == -1:
            return True
        return self.joborders.filter_by(is_admin_hidden=False).count() < max_jobs

    @property
    def storage_limit_mb(self):
        """Get storage limit based on plan"""
        from config import Config
        return Config.SUBSCRIPTION_PLANS[self.subscription_plan]['features']['storage_gb'] * 1024


# ============================================================================
# User Model
# ============================================================================

class User(UserMixin, TenantModel):
    """User model with authentication"""
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(128), nullable=False, index=True)
    password_hash = db.Column(db.String(255))

    # Profile
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    title = db.Column(db.String(128))
    phone_work = db.Column(db.String(40))
    phone_cell = db.Column(db.String(40))

    # Access Control
    access_level = db.Column(db.Integer, default=100, nullable=False)  # 100=read, 200=edit, 300=delete, 400=admin, 500=root
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    categories = db.Column(db.String(255))  # Comma-separated role categories

    # Preferences
    timezone = db.Column(db.String(50))
    date_format_dmy = db.Column(db.Boolean, default=False)
    items_per_page = db.Column(db.Integer, default=20)

    # Session
    last_login = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        """Required by Flask-Login"""
        return str(self.user_id)

    @property
    def full_name(self):
        """Get full name"""
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def is_admin(self):
        """Check if user is admin (400+)"""
        return self.access_level >= 400

    @property
    def is_root(self):
        """Check if user is root (500)"""
        return self.access_level >= 500

    def has_permission(self, permission):
        """Check if user has permission"""
        from app.utils.permissions import get_required_level
        required_level = get_required_level(permission)
        return self.access_level >= required_level

    def __repr__(self):
        return f'<User {self.username}>'


# ============================================================================
# Candidate Model
# ============================================================================

class Candidate(TenantModel):
    """Candidate/Applicant model"""
    __tablename__ = 'candidate'

    candidate_id = db.Column(db.Integer, primary_key=True)

    # Personal Information
    first_name = db.Column(db.String(50), nullable=False, index=True)
    middle_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50), nullable=False, index=True)

    # Contact Information
    email1 = db.Column(db.String(128), index=True)
    email2 = db.Column(db.String(128))
    phone_home = db.Column(db.String(40))
    phone_cell = db.Column(db.String(40))
    phone_work = db.Column(db.String(40))

    # Address
    address = db.Column(db.Text)
    city = db.Column(db.String(64), index=True)
    state = db.Column(db.String(64))
    zip = db.Column(db.String(16))
    country = db.Column(db.String(64))

    # Professional Information
    source = db.Column(db.String(64))
    key_skills = db.Column(db.Text)
    current_employer = db.Column(db.String(255))
    current_pay = db.Column(db.String(64))
    desired_pay = db.Column(db.String(64))
    date_available = db.Column(db.String(64))

    # Flags
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_admin_hidden = db.Column(db.Boolean, default=False, nullable=False)
    is_hot = db.Column(db.Boolean, default=False)
    can_relocate = db.Column(db.Boolean, default=False)

    # Notes
    notes = db.Column(db.Text)

    # EEO Information
    eeo_ethnic_type_id = db.Column(db.Integer)
    eeo_veteran_type_id = db.Column(db.Integer)
    eeo_disability_status = db.Column(db.String(64))
    eeo_gender = db.Column(db.String(16))

    # Relationships
    pipeline_entries = db.relationship('CandidateJobOrder', backref='candidate', lazy='dynamic')
    attachments = db.relationship('Attachment',
                                 primaryjoin='and_(Attachment.data_item_id==Candidate.candidate_id, '
                                            'Attachment.data_item_type==100)',
                                 foreign_keys='[Attachment.data_item_id]',
                                 backref='candidate',
                                 lazy='dynamic')

    @property
    def full_name(self):
        """Get full name"""
        parts = [self.first_name, self.middle_name, self.last_name]
        return ' '.join([p for p in parts if p])

    @property
    def primary_email(self):
        """Get primary email"""
        return self.email1 or self.email2

    @property
    def primary_phone(self):
        """Get primary phone"""
        return self.phone_cell or self.phone_work or self.phone_home

    def __repr__(self):
        return f'<Candidate {self.candidate_id}: {self.full_name}>'


# ============================================================================
# Company Model
# ============================================================================

class Company(TenantModel):
    """Company/Client model"""
    __tablename__ = 'company'

    company_id = db.Column(db.Integer, primary_key=True)

    # Basic Information
    name = db.Column(db.String(255), nullable=False, index=True)
    phone1 = db.Column(db.String(40))
    phone2 = db.Column(db.String(40))
    fax = db.Column(db.String(40))
    url = db.Column(db.String(255))

    # Address
    address = db.Column(db.Text)
    city = db.Column(db.String(64))
    state = db.Column(db.String(64))
    zip = db.Column(db.String(16))
    country = db.Column(db.String(64))

    # Details
    key_technologies = db.Column(db.Text)
    notes = db.Column(db.Text)

    # Flags
    is_hot = db.Column(db.Boolean, default=False)
    is_admin_hidden = db.Column(db.Boolean, default=False, nullable=False)

    # Billing
    billing_contact_id = db.Column(db.Integer, db.ForeignKey('contact.contact_id'))

    # Relationships
    contacts = db.relationship('Contact', backref='company', lazy='dynamic',
                              foreign_keys='Contact.company_id')
    joborders = db.relationship('JobOrder', backref='company', lazy='dynamic')
    departments = db.relationship('CompanyDepartment', backref='company', lazy='dynamic')

    def __repr__(self):
        return f'<Company {self.company_id}: {self.name}>'


class CompanyDepartment(TenantModel):
    """Company Department"""
    __tablename__ = 'company_department'

    company_department_id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.company_id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Department {self.name}>'


# ============================================================================
# Contact Model
# ============================================================================

class Contact(TenantModel):
    """Contact model - individuals at companies"""
    __tablename__ = 'contact'

    contact_id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.company_id'), nullable=False, index=True)
    company_department_id = db.Column(db.Integer, db.ForeignKey('company_department.company_department_id'))

    # Personal Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(128))

    # Contact Information
    email1 = db.Column(db.String(128))
    email2 = db.Column(db.String(128))
    phone_work = db.Column(db.String(40))
    phone_cell = db.Column(db.String(40))
    phone_other = db.Column(db.String(40))

    # Address
    address = db.Column(db.Text)
    city = db.Column(db.String(64))
    state = db.Column(db.String(64))
    zip = db.Column(db.String(16))

    # Details
    notes = db.Column(db.Text)
    is_hot = db.Column(db.Boolean, default=False)
    left_company = db.Column(db.Boolean, default=False)
    reports_to = db.Column(db.Integer, db.ForeignKey('contact.contact_id'))

    # Relationships
    joborders = db.relationship('JobOrder', backref='contact', lazy='dynamic')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f'<Contact {self.contact_id}: {self.full_name}>'


# ============================================================================
# Job Order Model
# ============================================================================

class JobOrder(TenantModel):
    """Job Order model"""
    __tablename__ = 'joborder'

    joborder_id = db.Column(db.Integer, primary_key=True)

    # Basic Information
    title = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text)
    notes = db.Column(db.Text)

    # Relationships
    company_id = db.Column(db.Integer, db.ForeignKey('company.company_id'), nullable=False, index=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.contact_id'))
    company_department_id = db.Column(db.Integer, db.ForeignKey('company_department.company_department_id'))
    recruiter = db.Column(db.Integer, db.ForeignKey('user.user_id'))

    # Job Details
    type = db.Column(db.Integer, default=1)  # 1=Permanent, 2=Contract, 3=Temporary, etc.
    duration = db.Column(db.String(64))
    rate_max = db.Column(db.String(64))
    salary = db.Column(db.String(64))

    # Location
    city = db.Column(db.String(64))
    state = db.Column(db.String(64))

    # Status
    status = db.Column(db.Integer, default=1, index=True)  # 1=Active, 2=On Hold, 3=Closed, 4=Filled
    openings = db.Column(db.Integer, default=1)
    openings_available = db.Column(db.Integer, default=1)

    # Dates
    start_date = db.Column(db.DateTime)

    # Flags
    is_hot = db.Column(db.Boolean, default=False)
    is_admin_hidden = db.Column(db.Boolean, default=False, nullable=False)
    public = db.Column(db.Boolean, default=False)  # Visible on career portal

    # Relationships
    pipeline_entries = db.relationship('CandidateJobOrder', backref='joborder', lazy='dynamic')

    def __repr__(self):
        return f'<JobOrder {self.joborder_id}: {self.title}>'


# ============================================================================
# Pipeline Model (Many-to-Many: Candidate <-> JobOrder)
# ============================================================================

class CandidateJobOrder(TenantModel):
    """Pipeline entry - links candidate to job order with status"""
    __tablename__ = 'candidate_joborder'

    candidate_joborder_id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.candidate_id'), nullable=False, index=True)
    joborder_id = db.Column(db.Integer, db.ForeignKey('joborder.joborder_id'), nullable=False, index=True)

    # Status
    status = db.Column(db.Integer, default=0)  # 0=No Contact, 200=Contacted, 400=Submitted, 800=Placed
    rating_value = db.Column(db.Integer, default=0)  # -6 to 5

    # Tracking
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.user_id'))

    def __repr__(self):
        return f'<Pipeline {self.candidate_id} -> {self.joborder_id}>'


# ============================================================================
# Attachment Model (Polymorphic)
# ============================================================================

class Attachment(TenantModel):
    """File attachment model - can attach to any entity"""
    __tablename__ = 'attachment'

    attachment_id = db.Column(db.Integer, primary_key=True)

    # Polymorphic relationship
    data_item_type = db.Column(db.Integer, nullable=False, index=True)  # 100=Candidate, 200=Company, 300=Contact, 400=JobOrder
    data_item_id = db.Column(db.Integer, nullable=False, index=True)

    # File Information
    title = db.Column(db.String(255))
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)  # bytes
    mime_type = db.Column(db.String(128))

    # Storage
    storage_type = db.Column(db.String(20), default='local')  # local, s3
    storage_path = db.Column(db.String(500))

    # Resume-specific
    is_resume = db.Column(db.Boolean, default=False)
    text_resume = db.Column(db.Text)  # Extracted text

    # Profile image
    is_profile_image = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Attachment {self.attachment_id}: {self.original_filename}>'


# ============================================================================
# Activity Model
# ============================================================================

class Activity(TenantModel):
    """Activity log - calls, emails, meetings"""
    __tablename__ = 'activity'

    activity_id = db.Column(db.Integer, primary_key=True)

    # Polymorphic relationship
    data_item_type = db.Column(db.Integer, index=True)
    data_item_id = db.Column(db.Integer, index=True)

    # Related job order (optional)
    joborder_id = db.Column(db.Integer, db.ForeignKey('joborder.joborder_id'))

    # Activity details
    type = db.Column(db.Integer, nullable=False)  # 100=Call, 200=Email, 300=Meeting, 400=Other
    notes = db.Column(db.Text)
    regarding = db.Column(db.String(255))

    def __repr__(self):
        return f'<Activity {self.activity_id}>'


# Event listeners for automatic timestamp updates
@event.listens_for(BaseModel, 'before_update', propagate=True)
def receive_before_update(mapper, connection, target):
    """Update date_modified before update"""
    target.date_modified = datetime.utcnow()
