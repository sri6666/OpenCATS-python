# OpenCATS Flask Rewrite Specification

**Version:** 1.0
**Date:** 2026-01-02
**Purpose:** Complete technical specification for rewriting OpenCATS from PHP to Python Flask/SQLAlchemy

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Database Schema](#database-schema)
4. [Core Features](#core-features)
5. [Authentication & Authorization](#authentication--authorization)
6. [API & AJAX Endpoints](#api--ajax-endpoints)
7. [UI & Frontend](#ui--frontend)
8. [Migration Strategy](#migration-strategy)
9. [Technology Stack Recommendations](#technology-stack-recommendations)
10. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

OpenCATS is a comprehensive PHP-based Applicant Tracking System (ATS) with:

- **81 library classes** (46,703 lines of PHP)
- **25 feature modules** for recruitment management
- **58 database tables** with complex relationships
- **32+ AJAX endpoints** for real-time interactions
- **136 template files** for UI rendering
- **Multi-tenant architecture** with role-based access control

This specification provides a complete blueprint for rewriting OpenCATS using modern Python technologies while preserving all functionality and improving architecture.

---

## 1. Architecture Overview

### 1.1 Current PHP Architecture

**Directory Structure:**
```
OpenCATS/
├── index.php                    # Main entry point
├── ajax.php                     # AJAX dispatcher
├── config.php                   # Configuration
├── constants.php                # Global constants
├── QueueCLI.php                # Background task processor
│
├── lib/                         # 81 core library classes (46,703 lines)
│   ├── DatabaseConnection.php   # DB abstraction (singleton)
│   ├── Session.php              # Session management (CATSSession)
│   ├── Users.php                # User authentication/management
│   ├── UserInterface.php        # Base controller class
│   ├── ModuleUtility.php        # Module discovery/loading
│   ├── Template.php             # Template rendering
│   ├── Candidates.php           # Candidate CRUD (2,473 lines)
│   ├── JobOrders.php            # Job order operations (1,294 lines)
│   ├── Companies.php            # Company management (994 lines)
│   ├── Contacts.php             # Contact operations (1,050 lines)
│   ├── Attachments.php          # File management (1,386 lines)
│   ├── Search.php               # Full-text search (2,096 lines)
│   └── [75+ more libraries]
│
├── modules/                     # 25 feature modules
│   ├── candidates/
│   │   ├── CandidatesUI.php    # Controller
│   │   ├── Add.tpl             # Templates
│   │   ├── Edit.tpl
│   │   ├── Show.tpl
│   │   ├── dataGrids.php       # Data grid configs
│   │   └── ajax/               # Module AJAX handlers
│   ├── joborders/
│   ├── companies/
│   ├── contacts/
│   ├── calendar/
│   ├── reports/
│   ├── settings/
│   └── [18 more modules]
│
├── src/OpenCATS/                # Modern PSR-4 code
│   ├── Entity/                  # Domain objects
│   │   ├── Company.php
│   │   ├── JobOrder.php
│   │   └── *Repository.php
│   ├── UI/
│   │   └── QuickActionMenu.php
│   └── Tests/
│
├── ajax/                        # 22 global AJAX handlers
├── db/                          # Database schemas
│   ├── cats_schema.sql         # Main schema (58 tables)
│   └── upgrade-*.sql           # Migration scripts
├── js/                          # JavaScript files
├── templates/                   # Template files (.tpl)
└── attachments/                 # Uploaded files
```

**Request Flow:**
```
HTTP Request
    ↓
index.php (entry point)
    ↓
config.php + constants.php loaded
    ↓
Core libraries loaded (dependency order)
    ↓
Session validation ($_SESSION['CATS'])
    ↓
ModuleUtility::loadModule($moduleName)
    ↓
Module Class instantiated (extends UserInterface)
    ↓
handleRequest() → routes to action method
    ↓
Action method:
  - Loads data via Model classes (e.g., Candidates)
  - Creates Template object
  - Assigns data to template
  - Renders template
    ↓
Response sent to browser
```

**URL Routing:**
- Format: `?m=module&a=action&id=value`
- Examples:
  - `?m=candidates&a=show&candidateID=55`
  - `?m=joborders&a=edit&jobOrderID=123`
  - `?m=home` (default dashboard)

**Module Pattern:**
```php
class CandidatesUI extends UserInterface {
    public function handleRequest() {
        $action = $this->getAction();

        switch ($action) {
            case 'show':
                $this->show();
                break;
            case 'add':
                if ($this->isPostBack())
                    $this->onAdd();
                else
                    $this->add();
                break;
        }
    }
}
```

### 1.2 Proposed Flask Architecture

**Project Structure:**
```
opencats_flask/
├── run.py                       # Application entry point
├── config.py                    # Configuration management
├── requirements.txt             # Python dependencies
│
├── app/
│   ├── __init__.py             # Flask app factory
│   ├── extensions.py           # Extension initialization (SQLAlchemy, etc.)
│   ├── models.py               # SQLAlchemy models (or models/)
│   ├── auth/                   # Authentication blueprint
│   │   ├── __init__.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   └── models.py
│   │
│   ├── candidates/             # Candidates blueprint
│   │   ├── __init__.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   └── templates/
│   │       ├── show.html
│   │       ├── edit.html
│   │       └── list.html
│   │
│   ├── joborders/              # Job orders blueprint
│   ├── companies/              # Companies blueprint
│   ├── contacts/               # Contacts blueprint
│   ├── calendar/               # Calendar blueprint
│   ├── reports/                # Reports blueprint
│   ├── api/                    # REST API blueprint
│   │   ├── __init__.py
│   │   ├── candidates.py
│   │   ├── companies.py
│   │   └── schemas.py          # Marshmallow schemas
│   │
│   ├── templates/              # Global templates
│   │   ├── base.html
│   │   ├── layout.html
│   │   └── components/
│   │       ├── navbar.html
│   │       ├── sidebar.html
│   │       └── footer.html
│   │
│   ├── static/                 # Static assets
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   │
│   └── utils/                  # Utilities
│       ├── decorators.py
│       ├── validators.py
│       ├── parsers.py          # Resume parsing
│       └── search.py           # Search utilities
│
├── migrations/                 # Alembic migrations
├── tests/                      # Test suite
│   ├── unit/
│   ├── integration/
│   └── conftest.py
│
└── uploads/                    # User uploads
```

**URL Routing (Flask):**
```python
# Blueprint-based routing
@candidates_bp.route('/')
def index():
    """List candidates"""

@candidates_bp.route('/<int:id>')
def show(id):
    """Show candidate details"""

@candidates_bp.route('/add', methods=['GET', 'POST'])
def add():
    """Add candidate"""

@candidates_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit candidate"""

# API routes
@api_bp.route('/api/candidates/<int:id>')
def get_candidate(id):
    """REST API endpoint"""
```

**Request Flow (Flask):**
```
HTTP Request
    ↓
Flask Router (URL dispatcher)
    ↓
Before Request Hooks
  - Session validation
  - CSRF token validation
  - Permission checks
    ↓
View Function (in blueprint)
    ↓
Business Logic:
  - Load data via SQLAlchemy models
  - Process forms (WTForms)
  - Permission checks (decorators)
    ↓
Render Template (Jinja2) OR Return JSON
    ↓
After Request Hooks
    ↓
Response sent to browser
```

---

## 2. Database Schema

### 2.1 Database Overview

- **Engine:** MySQL/MariaDB (MyISAM → InnoDB recommended)
- **Charset:** UTF-8 (utf8_unicode_ci)
- **Total Tables:** 58
- **Multi-tenancy:** All tables have `site_id` foreign key

### 2.2 Table Categories

#### Core Business Entities (9 tables)
1. **candidate** - Job applicants/candidates
2. **company** - Client companies
3. **contact** - Company contacts
4. **joborder** - Job positions to fill
5. **candidate_joborder** - Pipeline entries (M2M)
6. **candidate_joborder_status** - Pipeline status definitions
7. **candidate_joborder_status_history** - Audit trail
8. **company_department** - Departments within companies
9. **candidate_source** - Candidate source tracking

#### User & Authentication (3 tables)
10. **user** - System users
11. **user_login** - Login history
12. **access_level** - Permission definitions

#### Multi-tenancy (1 table)
13. **site** - Site/tenant configuration

#### Activities & Communication (6 tables)
14. **activity** - Activity log
15. **activity_type** - Activity type definitions
16. **calendar_event** - Calendar events
17. **calendar_event_type** - Event types
18. **email_history** - Email log
19. **email_template** - Email templates

#### Document Management (2 tables)
20. **attachment** - File attachments
21. **extra_field** - Custom field values
22. **extra_field_settings** - Custom field definitions

#### Career Portal (6 tables)
23. **career_portal_questionnaire**
24. **career_portal_questionnaire_question**
25. **career_portal_questionnaire_answer**
26. **career_portal_questionnaire_history**
27. **career_portal_template**
28. **career_portal_template_site**

#### Lists & Search (4 tables)
29. **saved_list**
30. **saved_list_entry**
31. **saved_search**
32. **mru** - Most Recently Used

#### System & Configuration (8 tables)
33. **settings** - Configuration key-value pairs
34. **system** - System metadata
35. **module_schema** - Module version tracking
36. **queue** - Async task queue
37. **history** - Change audit trail
38. **http_log** - HTTP request logging
39. **http_log_types** - Log type definitions
40. **installtest** - Installation verification

#### Data Types & Lookups (5 tables)
41. **data_item_type** - Entity type enum
42. **tag** - Hierarchical tags
43. **candidate_tag** - Tag assignments
44. **candidate_duplicates** - Duplicate tracking
45. **eeo_ethnic_type** - EEO ethnicity options
46. **eeo_veteran_type** - EEO veteran options

#### Import/Export & Feeds (5 tables)
47. **import** - Import job tracking
48. **xml_feeds** - XML feed definitions
49. **xml_feed_submits** - Feed submissions
50. **word_verification** - CAPTCHA words
51. **zipcodes** - US ZIP code database

#### Miscellaneous (7 tables)
52. **sph_counter** - Sphinx search counter
53. **feedback** - User feedback
54. **extension_statistics** - Usage stats

### 2.3 Key Tables Detail

#### **candidate** Table
```sql
CREATE TABLE candidate (
  candidate_id INT(11) AUTO_INCREMENT PRIMARY KEY,
  site_id INT(11) NOT NULL,
  first_name VARCHAR(50),
  middle_name VARCHAR(50),
  last_name VARCHAR(50),
  email1 VARCHAR(128),
  email2 VARCHAR(128),
  phone_home VARCHAR(40),
  phone_cell VARCHAR(40),
  phone_work VARCHAR(40),
  address TEXT,
  city VARCHAR(64),
  state VARCHAR(64),
  zip VARCHAR(16),
  source VARCHAR(64),
  key_skills TEXT,
  current_employer VARCHAR(255),
  current_pay VARCHAR(64),
  desired_pay VARCHAR(64),
  is_active INT(1) DEFAULT 1,
  is_admin_hidden INT(1) DEFAULT 0,
  is_hot INT(1) DEFAULT 0,
  can_relocate INT(1) DEFAULT 0,
  notes TEXT,
  date_available VARCHAR(64),
  date_created DATETIME,
  date_modified DATETIME,
  entered_by INT(11),
  owner INT(11),
  INDEX idx_site_first_last_modified (site_id, first_name, last_name, date_modified),
  INDEX idx_site_email (site_id, email1(8), email2(8))
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
```

**SQLAlchemy Model:**
```python
class Candidate(db.Model):
    __tablename__ = 'candidate'

    candidate_id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey('site.site_id'), nullable=False)
    first_name = db.Column(db.String(50))
    middle_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email1 = db.Column(db.String(128))
    email2 = db.Column(db.String(128))
    phone_home = db.Column(db.String(40))
    phone_cell = db.Column(db.String(40))
    phone_work = db.Column(db.String(40))
    address = db.Column(db.Text)
    city = db.Column(db.String(64))
    state = db.Column(db.String(64))
    zip = db.Column(db.String(16))
    source = db.Column(db.String(64))
    key_skills = db.Column(db.Text)
    current_employer = db.Column(db.String(255))
    current_pay = db.Column(db.String(64))
    desired_pay = db.Column(db.String(64))
    is_active = db.Column(db.Boolean, default=True)
    is_admin_hidden = db.Column(db.Boolean, default=False)
    is_hot = db.Column(db.Boolean, default=False)
    can_relocate = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    date_available = db.Column(db.String(64))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    entered_by = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    owner = db.Column(db.Integer, db.ForeignKey('user.user_id'))

    # Relationships
    site = db.relationship('Site', backref='candidates')
    pipeline_entries = db.relationship('CandidateJobOrder', backref='candidate', lazy='dynamic')
    attachments = db.relationship('Attachment',
                                 primaryjoin='and_(Attachment.data_item_id==Candidate.candidate_id, '
                                            'Attachment.data_item_type==100)',
                                 foreign_keys='[Attachment.data_item_id]',
                                 backref='candidate')
    activities = db.relationship('Activity',
                                primaryjoin='and_(Activity.data_item_id==Candidate.candidate_id, '
                                           'Activity.data_item_type==100)',
                                foreign_keys='[Activity.data_item_id]',
                                backref='candidate')
    tags = db.relationship('CandidateTag', backref='candidate', lazy='dynamic')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f'<Candidate {self.candidate_id}: {self.full_name}>'
```

#### **joborder** Table
```sql
CREATE TABLE joborder (
  joborder_id INT(11) AUTO_INCREMENT PRIMARY KEY,
  site_id INT(11) NOT NULL,
  recruiter INT(11),
  contact_id INT(11),
  company_id INT(11),
  company_department_id INT(11),
  title VARCHAR(255),
  description TEXT,
  notes TEXT,
  type INT(11),
  duration VARCHAR(64),
  rate_max VARCHAR(64),
  salary VARCHAR(64),
  status INT(11),
  is_hot INT(1) DEFAULT 0,
  is_admin_hidden INT(1) DEFAULT 0,
  openings INT(11),
  openings_available INT(11),
  city VARCHAR(64),
  state VARCHAR(64),
  start_date DATETIME,
  date_created DATETIME,
  date_modified DATETIME,
  entered_by INT(11),
  owner INT(11),
  public INT(1) DEFAULT 0,
  INDEX idx_site_status (site_id, status)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
```

**SQLAlchemy Model:**
```python
class JobOrder(db.Model):
    __tablename__ = 'joborder'

    joborder_id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey('site.site_id'), nullable=False)
    recruiter = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.contact_id'))
    company_id = db.Column(db.Integer, db.ForeignKey('company.company_id'))
    company_department_id = db.Column(db.Integer, db.ForeignKey('company_department.company_department_id'))
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    notes = db.Column(db.Text)
    type = db.Column(db.Integer)  # Permanent, Contract, etc.
    duration = db.Column(db.String(64))
    rate_max = db.Column(db.String(64))
    salary = db.Column(db.String(64))
    status = db.Column(db.Integer)  # Open, Closed, On Hold
    is_hot = db.Column(db.Boolean, default=False)
    is_admin_hidden = db.Column(db.Boolean, default=False)
    openings = db.Column(db.Integer)
    openings_available = db.Column(db.Integer)
    city = db.Column(db.String(64))
    state = db.Column(db.String(64))
    start_date = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    entered_by = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    owner = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    public = db.Column(db.Boolean, default=False)

    # Relationships
    site = db.relationship('Site', backref='joborders')
    company = db.relationship('Company', backref='joborders')
    contact = db.relationship('Contact', backref='joborders')
    department = db.relationship('CompanyDepartment', backref='joborders')
    pipeline_entries = db.relationship('CandidateJobOrder', backref='joborder', lazy='dynamic')
```

#### **candidate_joborder** (Pipeline) Table
```sql
CREATE TABLE candidate_joborder (
  candidate_joborder_id INT(11) AUTO_INCREMENT PRIMARY KEY,
  site_id INT(11) NOT NULL,
  candidate_id INT(11),
  joborder_id INT(11),
  status INT(11),
  date_created DATETIME,
  date_modified DATETIME,
  rating_value INT(11) DEFAULT 0,
  submitted_by INT(11),
  INDEX idx_candidate_joborder (candidate_id, joborder_id),
  INDEX idx_joborder_status (joborder_id, status)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
```

**SQLAlchemy Model:**
```python
class CandidateJobOrder(db.Model):
    """Pipeline entry - links candidate to job order with status"""
    __tablename__ = 'candidate_joborder'

    candidate_joborder_id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey('site.site_id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.candidate_id'))
    joborder_id = db.Column(db.Integer, db.ForeignKey('joborder.joborder_id'))
    status = db.Column(db.Integer, db.ForeignKey('candidate_joborder_status.candidate_joborder_status_id'))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    rating_value = db.Column(db.Integer, default=0)  # -6 to 5
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.user_id'))

    # Relationships
    status_obj = db.relationship('CandidateJobOrderStatus', foreign_keys=[status])
    history = db.relationship('CandidateJobOrderStatusHistory', backref='pipeline_entry', lazy='dynamic')
```

### 2.4 Entity Relationships

```
SITE (Multi-tenant root)
  └─> USER
  └─> CANDIDATE
      ├─> CANDIDATE_JOBORDER (Pipeline)
      │   ├─> JOBORDER
      │   ├─> CANDIDATE_JOBORDER_STATUS
      │   └─> CANDIDATE_JOBORDER_STATUS_HISTORY
      ├─> CANDIDATE_TAG → TAG
      ├─> CANDIDATE_SOURCE
      └─> CANDIDATE_DUPLICATES

  └─> COMPANY
      ├─> COMPANY_DEPARTMENT
      ├─> CONTACT
      │   └─> JOBORDER
      └─> JOBORDER

  └─> ATTACHMENT (polymorphic: candidate, company, contact, joborder)
  └─> ACTIVITY (polymorphic)
  └─> EXTRA_FIELD (polymorphic)
  └─> HISTORY (polymorphic audit trail)
  └─> CALENDAR_EVENT
  └─> EMAIL_HISTORY
  └─> SAVED_LIST → SAVED_LIST_ENTRY
  └─> SAVED_SEARCH
```

### 2.5 SQLAlchemy Base Configuration

```python
# app/models/__init__.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Base model with common fields
class BaseModel(db.Model):
    __abstract__ = True

    site_id = db.Column(db.Integer, db.ForeignKey('site.site_id'), nullable=False, index=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    date_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    entered_by = db.Column(db.Integer, db.ForeignKey('user.user_id'))

    # Multi-tenancy filter
    @classmethod
    def query_for_site(cls, site_id):
        return cls.query.filter_by(site_id=site_id)
```

---

## 3. Core Features

### 3.1 Candidates/Applicants Module

**Files (PHP):**
- Controller: `/modules/candidates/CandidatesUI.php` (135KB)
- Model: `/lib/Candidates.php` (2,473 lines)
- Templates: `Add.tpl`, `Edit.tpl`, `Show.tpl`, `Search.tpl`, `Duplicates.tpl`

**Key Operations:**
1. **CRUD**
   - Create candidate with full profile
   - Edit all fields including EEO data
   - Soft delete (is_admin_hidden flag)
   - View candidate details with related data

2. **Resume Management**
   - Upload multiple resumes (PDF, DOC, DOCX, RTF)
   - Text extraction via external tools (pdftotext, antiword)
   - Auto-populate fields from parsed resume
   - Resume viewing/download

3. **Search**
   - Full name search
   - Email/phone lookup
   - Key skills search
   - City-based search
   - Global keyword search

4. **Duplicate Detection**
   - Automatic duplicate checking on add/edit
   - Manual duplicate linking
   - Merge duplicates with field reconciliation
   - Preserve related data (lists, pipelines, activities)

5. **Pipeline Management**
   - Add to job orders
   - Track status through workflow
   - Rate candidates (1-5 scale)
   - Status history tracking

6. **Activities**
   - Log calls, emails, meetings
   - Link to candidates and/or jobs
   - Activity history display

7. **Attachments**
   - Multiple file uploads
   - Profile image uploads
   - Document attachments with metadata

8. **Tagging**
   - Hierarchical tag system
   - Multiple tags per candidate
   - Tag-based filtering

**Flask Implementation:**
```python
# app/candidates/views.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.candidates.forms import CandidateForm, CandidateSearchForm
from app.models import Candidate, Attachment
from app.utils.decorators import permission_required

candidates_bp = Blueprint('candidates', __name__, url_prefix='/candidates')

@candidates_bp.route('/')
@login_required
@permission_required('candidates.view')
def index():
    """List all candidates with pagination and filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = 15

    query = Candidate.query_for_site(current_user.site_id)
    query = query.filter_by(is_admin_hidden=False)

    # Apply filters from request args
    if request.args.get('search'):
        search = f"%{request.args.get('search')}%"
        query = query.filter(
            db.or_(
                Candidate.first_name.like(search),
                Candidate.last_name.like(search),
                Candidate.email1.like(search)
            )
        )

    pagination = query.paginate(page=page, per_page=per_page)

    return render_template('candidates/index.html',
                         candidates=pagination.items,
                         pagination=pagination)

@candidates_bp.route('/<int:id>')
@login_required
@permission_required('candidates.view')
def show(id):
    """Show candidate details"""
    candidate = Candidate.query_for_site(current_user.site_id).get_or_404(id)

    # Load related data
    pipeline_entries = candidate.pipeline_entries.all()
    activities = candidate.activities.order_by(Activity.date_created.desc()).limit(10).all()
    attachments = candidate.attachments.all()

    return render_template('candidates/show.html',
                         candidate=candidate,
                         pipeline_entries=pipeline_entries,
                         activities=activities,
                         attachments=attachments)

@candidates_bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('candidates.add')
def add():
    """Add new candidate"""
    form = CandidateForm()

    if form.validate_on_submit():
        # Check for duplicates
        duplicates = check_duplicates(form.email1.data, form.phone_cell.data)
        if duplicates and not request.form.get('ignore_duplicates'):
            flash('Potential duplicates found. Please review.', 'warning')
            return render_template('candidates/duplicates.html',
                                 form=form,
                                 duplicates=duplicates)

        candidate = Candidate(
            site_id=current_user.site_id,
            entered_by=current_user.user_id,
            owner=current_user.user_id
        )
        form.populate_obj(candidate)

        db.session.add(candidate)
        db.session.commit()

        flash(f'Candidate {candidate.full_name} added successfully.', 'success')
        return redirect(url_for('candidates.show', id=candidate.candidate_id))

    return render_template('candidates/add.html', form=form)

@candidates_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('candidates.edit')
def edit(id):
    """Edit candidate"""
    candidate = Candidate.query_for_site(current_user.site_id).get_or_404(id)
    form = CandidateForm(obj=candidate)

    if form.validate_on_submit():
        form.populate_obj(candidate)
        candidate.date_modified = datetime.utcnow()

        db.session.commit()

        # Log change to history
        log_history(candidate, 'updated', current_user.user_id)

        flash(f'Candidate {candidate.full_name} updated successfully.', 'success')
        return redirect(url_for('candidates.show', id=candidate.candidate_id))

    return render_template('candidates/edit.html', form=form, candidate=candidate)

@candidates_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('candidates.delete')
def delete(id):
    """Delete (hide) candidate"""
    candidate = Candidate.query_for_site(current_user.site_id).get_or_404(id)
    candidate.is_admin_hidden = True

    db.session.commit()

    flash(f'Candidate {candidate.full_name} deleted.', 'success')
    return redirect(url_for('candidates.index'))

# Resume parsing endpoint
@candidates_bp.route('/parse-resume', methods=['POST'])
@login_required
def parse_resume():
    """Parse uploaded resume and return extracted data"""
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['resume']

    # Extract text from document
    from app.utils.parsers import ResumeParser
    parser = ResumeParser(file)
    extracted_data = parser.parse()

    return jsonify(extracted_data)
```

**Forms (WTForms):**
```python
# app/candidates/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Optional

class CandidateForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email1 = StringField('Email', validators=[DataRequired(), Email()])
    email2 = StringField('Secondary Email', validators=[Optional(), Email()])
    phone_home = StringField('Home Phone')
    phone_cell = StringField('Cell Phone')
    phone_work = StringField('Work Phone')
    address = TextAreaField('Address')
    city = StringField('City')
    state = StringField('State')
    zip = StringField('ZIP Code')
    source = StringField('Source')
    key_skills = TextAreaField('Key Skills')
    current_employer = StringField('Current Employer')
    current_pay = StringField('Current Pay')
    desired_pay = StringField('Desired Pay')
    can_relocate = BooleanField('Can Relocate')
    is_hot = BooleanField('Hot Candidate')
    notes = TextAreaField('Notes')
```

### 3.2 Job Orders Module

**Key Operations:**
1. **Job Management**
   - Create job orders with title, description, requirements
   - Set type (Permanent, Contract, Temporary, etc.)
   - Track status (Active, On Hold, Closed, Filled)
   - Openings tracking (total vs available)

2. **Pipeline Management**
   - Add candidates to pipeline
   - Track candidates through stages
   - Update statuses
   - Rate candidate fit

3. **Pipeline Stages:**
   - No Contact (0)
   - Contacted (200)
   - Candidate Responded (250)
   - Qualifying (300)
   - Submitted (400)
   - Interviewing (500)
   - Offered (600)
   - Not in Consideration (650)
   - Client Declined (700)
   - Placed (800)

**Flask Implementation:**
```python
# app/joborders/views.py
@joborders_bp.route('/<int:id>/pipeline')
@login_required
def pipeline(id):
    """View job order pipeline"""
    joborder = JobOrder.query_for_site(current_user.site_id).get_or_404(id)

    # Group candidates by status
    pipeline_by_status = {}
    for entry in joborder.pipeline_entries:
        status_name = entry.status_obj.short_description
        if status_name not in pipeline_by_status:
            pipeline_by_status[status_name] = []
        pipeline_by_status[status_name].append(entry)

    return render_template('joborders/pipeline.html',
                         joborder=joborder,
                         pipeline=pipeline_by_status)

@joborders_bp.route('/<int:job_id>/add-candidate/<int:candidate_id>', methods=['POST'])
@login_required
def add_candidate_to_pipeline(job_id, candidate_id):
    """Add candidate to job pipeline"""
    joborder = JobOrder.query_for_site(current_user.site_id).get_or_404(job_id)
    candidate = Candidate.query_for_site(current_user.site_id).get_or_404(candidate_id)

    # Check if already in pipeline
    existing = CandidateJobOrder.query.filter_by(
        candidate_id=candidate_id,
        joborder_id=job_id
    ).first()

    if existing:
        flash('Candidate already in pipeline.', 'warning')
        return redirect(url_for('joborders.pipeline', id=job_id))

    # Create pipeline entry
    pipeline_entry = CandidateJobOrder(
        site_id=current_user.site_id,
        candidate_id=candidate_id,
        joborder_id=job_id,
        status=0,  # No Contact
        submitted_by=current_user.user_id
    )

    db.session.add(pipeline_entry)
    db.session.commit()

    flash(f'{candidate.full_name} added to pipeline.', 'success')
    return redirect(url_for('joborders.pipeline', id=job_id))
```

### 3.3 Companies Module

**Key Operations:**
1. Company CRUD (name, address, phones, URL, notes)
2. Department management
3. Contact associations
4. Job order tracking
5. Default company setting

### 3.4 Contacts Module

**Key Operations:**
1. Contact CRUD (name, title, email, phones)
2. Company linking
3. Department assignment
4. Cold call list generation
5. Activity tracking

### 3.5 Calendar/Activities Module

**Key Operations:**
1. Calendar event creation (type, date/time, duration)
2. Event types: Call, Email, Meeting, Interview
3. Reminders with email notifications
4. Activity logging (calls, emails, meetings)
5. Activity history by entity

### 3.6 Reports Module

**Report Types:**
1. Dashboard statistics
2. Job order reports
3. Submission reports
4. Placement reports
5. EEO reports
6. New data items report
7. Custom date range reports

**Flask Implementation:**
```python
# app/reports/views.py
@reports_bp.route('/dashboard')
@login_required
def dashboard():
    """Main reports dashboard"""
    site_id = current_user.site_id

    stats = {
        'candidates_total': Candidate.query_for_site(site_id).count(),
        'candidates_today': Candidate.query_for_site(site_id).filter(
            Candidate.date_created >= datetime.utcnow().date()
        ).count(),
        'joborders_open': JobOrder.query_for_site(site_id).filter_by(status=1).count(),
        'placements_month': CandidateJobOrder.query_for_site(site_id).filter(
            CandidateJobOrder.status == 800,  # Placed
            CandidateJobOrder.date_modified >= first_day_of_month()
        ).count(),
    }

    return render_template('reports/dashboard.html', stats=stats)
```

### 3.7 Search Module

**Search Types:**
1. **Candidate Search:** name, email, phone, skills, city
2. **Company Search:** name, technologies
3. **Job Order Search:** title, company, status
4. **Contact Search:** name, company, title
5. **Global Search:** across all entities
6. **Saved Searches:** store and re-run searches

**Flask Implementation:**
```python
# app/search/views.py
from sqlalchemy import or_

@search_bp.route('/candidates')
@login_required
def search_candidates():
    """Search candidates"""
    query = request.args.get('q', '')

    results = Candidate.query_for_site(current_user.site_id).filter(
        or_(
            Candidate.first_name.like(f'%{query}%'),
            Candidate.last_name.like(f'%{query}%'),
            Candidate.email1.like(f'%{query}%'),
            Candidate.key_skills.like(f'%{query}%')
        )
    ).limit(50).all()

    return render_template('search/results.html',
                         results=results,
                         query=query,
                         entity_type='candidate')
```

### 3.8 Email Integration

**Features:**
1. SMTP configuration (mail, sendmail, SMTP)
2. Email templates with variables
3. Status change notifications
4. Assignment notifications
5. Email history logging
6. Async email queue

**Flask Implementation:**
```python
# app/utils/email.py
from flask_mail import Mail, Message
from flask import current_app, render_template

mail = Mail()

def send_email(to, subject, template, **kwargs):
    """Send email using template"""
    msg = Message(
        subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[to]
    )
    msg.body = render_template(f'email/{template}.txt', **kwargs)
    msg.html = render_template(f'email/{template}.html', **kwargs)

    mail.send(msg)

    # Log to email_history
    log_email(to, subject, msg.body)

# Template variables replacement
def replace_template_vars(text, candidate=None, joborder=None, user=None):
    """Replace template variables like %CANDFULLNAME%"""
    replacements = {}

    if candidate:
        replacements['%CANDFULLNAME%'] = candidate.full_name
        replacements['%CANDFIRSTNAME%'] = candidate.first_name
        replacements['%CANDEMAIL%'] = candidate.email1

    if joborder:
        replacements['%JBODTITLE%'] = joborder.title
        replacements['%JBODCLIENT%'] = joborder.company.name

    if user:
        replacements['%USERFULLNAME%'] = user.full_name
        replacements['%USEREMAIL%'] = user.email

    for var, value in replacements.items():
        text = text.replace(var, value or '')

    return text
```

### 3.9 Document Handling

**Features:**
1. File upload (resume, documents, images)
2. Resume parsing (PDF, DOC, DOCX, RTF, ODT)
3. Text extraction
4. Multiple attachments per entity
5. Profile image management
6. Download/view attachments

**Flask Implementation:**
```python
# app/utils/parsers.py
import pdfplumber
from docx import Document
import re

class ResumeParser:
    def __init__(self, file):
        self.file = file
        self.filename = file.filename
        self.extension = self.filename.rsplit('.', 1)[1].lower()

    def parse(self):
        """Extract text and parse resume"""
        text = self.extract_text()

        # Parse extracted text
        data = {
            'name': self.extract_name(text),
            'email': self.extract_email(text),
            'phone': self.extract_phone(text),
            'skills': self.extract_skills(text),
        }

        return data

    def extract_text(self):
        """Extract text from document"""
        if self.extension == 'pdf':
            return self.extract_from_pdf()
        elif self.extension in ['doc', 'docx']:
            return self.extract_from_docx()
        elif self.extension == 'txt':
            return self.file.read().decode('utf-8')
        else:
            raise ValueError(f'Unsupported file type: {self.extension}')

    def extract_from_pdf(self):
        """Extract text from PDF"""
        text = ''
        with pdfplumber.open(self.file) as pdf:
            for page in pdf.pages:
                text += page.extract_text()
        return text

    def extract_from_docx(self):
        """Extract text from DOCX"""
        doc = Document(self.file)
        return '\n'.join([para.text for para in doc.paragraphs])

    def extract_email(self, text):
        """Extract email from text"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def extract_phone(self, text):
        """Extract phone from text"""
        pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        match = re.search(pattern, text)
        return match.group(0) if match else None
```

### 3.10 Import/Export

**Import Features:**
1. Candidate CSV import
2. Company CSV import
3. Bulk resume import (ZIP)
4. Field mapping wizard
5. Preview before commit
6. Error logging

**Export Features:**
1. CSV export (candidates, companies, contacts)
2. Excel export
3. XML job feeds
4. PDF reports

**Flask Implementation:**
```python
# app/import_export/views.py
import csv
from io import StringIO

@import_export_bp.route('/import/candidates', methods=['GET', 'POST'])
@login_required
@permission_required('import.candidates')
def import_candidates():
    """Import candidates from CSV"""
    if request.method == 'POST':
        file = request.files['csv_file']

        # Read CSV
        csv_data = file.read().decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_data))

        imported = 0
        errors = []

        for row in csv_reader:
            try:
                candidate = Candidate(
                    site_id=current_user.site_id,
                    first_name=row.get('first_name'),
                    last_name=row.get('last_name'),
                    email1=row.get('email'),
                    phone_cell=row.get('phone'),
                    entered_by=current_user.user_id,
                    owner=current_user.user_id
                )

                db.session.add(candidate)
                imported += 1
            except Exception as e:
                errors.append(f"Row {csv_reader.line_num}: {str(e)}")

        db.session.commit()

        flash(f'Imported {imported} candidates. {len(errors)} errors.', 'success')
        return render_template('import/results.html', errors=errors)

    return render_template('import/candidates.html')

@import_export_bp.route('/export/candidates')
@login_required
def export_candidates():
    """Export candidates to CSV"""
    candidates = Candidate.query_for_site(current_user.site_id).all()

    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(['ID', 'First Name', 'Last Name', 'Email', 'Phone', 'City', 'State'])

    # Data
    for candidate in candidates:
        writer.writerow([
            candidate.candidate_id,
            candidate.first_name,
            candidate.last_name,
            candidate.email1,
            candidate.phone_cell,
            candidate.city,
            candidate.state
        ])

    # Return as download
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=candidates.csv'
    response.headers['Content-Type'] = 'text/csv'

    return response
```

---

## 4. Authentication & Authorization

### 4.1 Authentication System

**Current PHP Implementation:**

**Login Flow:**
1. User submits username/password
2. System validates credentials (SQL or LDAP)
3. Password compared: `md5(input) == stored_hash`
4. Session created with user data
5. Session cookie set (HTTPOnly, Secure)
6. Login logged to `user_login` table
7. Redirect to dashboard

**Authentication Modes:**
- **SQL:** Database-only authentication
- **LDAP:** LDAP server authentication
- **SQL+LDAP:** Try LDAP, auto-create disabled users

**Password Storage:**
- MD5 hash (⚠️ INSECURE - needs upgrading)
- LDAP users: stored as `_LDAPUSER_` marker

**Session Management:**
- PHP session with `CATSSession` object
- Session data: user ID, site ID, access level, preferences
- Forced logout capability
- Single session mode (optional)

**Flask Implementation:**

```python
# app/auth/models.py
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey('site.site_id'), nullable=False)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(128))
    password_hash = db.Column(db.String(255))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    access_level = db.Column(db.Integer, default=100)
    is_active = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        """Hash password using bcrypt"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        """Required by Flask-Login"""
        return str(self.user_id)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def has_permission(self, permission):
        """Check if user has permission"""
        return self.access_level >= get_required_level(permission)

# app/auth/views.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.auth.forms import LoginForm
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login'))

        if not user.is_active:
            flash('Account is disabled', 'error')
            return redirect(url_for('auth.login'))

        # Log user in
        login_user(user, remember=form.remember_me.data)

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Log login to user_login table
        log_login(user.user_id, request.remote_addr, request.user_agent.string)

        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')

        return redirect(next_page)

    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

# app/__init__.py - Initialize Flask-Login
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
```

### 4.2 Authorization System

**Access Levels:**
```python
ACCESS_LEVEL_DELETED = -100    # Deleted user
ACCESS_LEVEL_DISABLED = 0      # Disabled account
ACCESS_LEVEL_READ = 100        # Read-only
ACCESS_LEVEL_EDIT = 200        # Edit capability
ACCESS_LEVEL_DELETE = 300      # Delete capability
ACCESS_LEVEL_DEMO = 350        # Demo user
ACCESS_LEVEL_SA = 400          # Site Administrator
ACCESS_LEVEL_MULTI_SA = 450    # Multi-tenant SA
ACCESS_LEVEL_ROOT = 500        # Root administrator
```

**Permission System:**
```python
# app/utils/decorators.py
from functools import wraps
from flask import abort
from flask_login import current_user

def permission_required(permission):
    """Decorator to check user permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)

            required_level = get_required_level(permission)
            if current_user.access_level < required_level:
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Permission mapping
PERMISSIONS = {
    'candidates.view': ACCESS_LEVEL_READ,
    'candidates.add': ACCESS_LEVEL_EDIT,
    'candidates.edit': ACCESS_LEVEL_EDIT,
    'candidates.delete': ACCESS_LEVEL_DELETE,
    'joborders.view': ACCESS_LEVEL_READ,
    'joborders.add': ACCESS_LEVEL_EDIT,
    'settings.manage': ACCESS_LEVEL_SA,
}

def get_required_level(permission):
    """Get required access level for permission"""
    return PERMISSIONS.get(permission, ACCESS_LEVEL_READ)

# Usage in views
@candidates_bp.route('/add')
@login_required
@permission_required('candidates.add')
def add():
    """Add candidate - requires EDIT level"""
    pass
```

**ACL (Access Control Lists):**
```python
# app/models/acl.py
class ACL(db.Model):
    """Access Control List for fine-grained permissions"""
    __tablename__ = 'acl'

    acl_id = db.Column(db.Integer, primary_key=True)
    user_category = db.Column(db.String(64))  # Role/category
    secured_object = db.Column(db.String(128))  # Module.action
    access_level = db.Column(db.Integer)

    @staticmethod
    def get_access_level(user_categories, secured_object, default_level):
        """Get access level for user category and object"""
        # Check exact match
        acl = ACL.query.filter_by(
            user_category=user_categories[0] if user_categories else '',
            secured_object=secured_object
        ).first()

        if acl:
            return acl.access_level

        # Check parent objects (e.g., 'candidates' for 'candidates.add')
        parts = secured_object.split('.')
        while len(parts) > 1:
            parts.pop()
            parent = '.'.join(parts)
            acl = ACL.query.filter_by(
                user_category=user_categories[0],
                secured_object=parent
            ).first()
            if acl:
                return acl.access_level

        # Return default
        return default_level
```

### 4.3 Security Improvements

**Upgrade from MD5 to bcrypt/PBKDF2:**
```python
# Migration script
def upgrade_passwords():
    """Upgrade from MD5 to bcrypt"""
    users = User.query.all()

    for user in users:
        if user.password_hash and len(user.password_hash) == 32:
            # MD5 hash detected (32 characters)
            # Mark for password reset
            user.password_reset_required = True
            db.session.commit()
```

**CSRF Protection:**
```python
# app/__init__.py
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

# In form templates
{{ form.csrf_token }}
```

**Rate Limiting:**
```python
# app/auth/views.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Login with rate limiting"""
    pass
```

---

## 5. API & AJAX Endpoints

### 5.1 Current AJAX System (PHP)

**Dispatcher:** `/ajax.php`
**Request Format:** `POST f=functionName&param1=value1`
**Response Format:** XML

**Example:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<data>
    <errorcode>0</errorcode>
    <errormessage></errormessage>
    <result>Data here</result>
</data>
```

**Core AJAX Endpoints (22 files):**
1. `getCandidateIdByEmail.php`
2. `getCandidateIdByPhone.php`
3. `getCompanyNames.php` (autocomplete)
4. `getCompanyContacts.php`
5. `getCompanyLocation.php`
6. `deleteActivity.php`
7. `editActivity.php`
8. `setCandidateJobOrderRating.php`
9. `getPipelineDetails.php`
10. `getPipelineJobOrder.php`
11. `getDataItemJobOrders.php`
12. `getDataGridPager.php`
13. `getParsedAddress.php`
14. `zipLookup.php`
15. `replaceTemplateTags.php`
16. `showTemplate.php`
17. `testEmailSettings.php`
18. `setColumnWidth.php`
19. `getAttachmentLocal.php`
20. Plus module-specific AJAX in `/modules/*/ajax/`

### 5.2 Proposed REST API (Flask)

**API Blueprint Structure:**
```python
# app/api/__init__.py
from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

from app.api import candidates, joborders, companies, contacts, auth
```

**RESTful Endpoints:**
```python
# app/api/candidates.py
from flask import jsonify, request
from flask_login import login_required
from app.models import Candidate
from app.api.schemas import CandidateSchema

candidate_schema = CandidateSchema()
candidates_schema = CandidateSchema(many=True)

@api_bp.route('/candidates', methods=['GET'])
@login_required
def get_candidates():
    """Get all candidates (paginated)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Candidate.query_for_site(current_user.site_id)

    # Filtering
    if request.args.get('search'):
        search = f"%{request.args.get('search')}%"
        query = query.filter(
            db.or_(
                Candidate.first_name.like(search),
                Candidate.last_name.like(search)
            )
        )

    pagination = query.paginate(page=page, per_page=per_page)

    return jsonify({
        'candidates': candidates_schema.dump(pagination.items),
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

@api_bp.route('/candidates/<int:id>', methods=['GET'])
@login_required
def get_candidate(id):
    """Get single candidate"""
    candidate = Candidate.query_for_site(current_user.site_id).get_or_404(id)
    return jsonify(candidate_schema.dump(candidate))

@api_bp.route('/candidates', methods=['POST'])
@login_required
@permission_required('candidates.add')
def create_candidate():
    """Create new candidate"""
    data = request.get_json()

    # Validate
    errors = candidate_schema.validate(data)
    if errors:
        return jsonify({'errors': errors}), 400

    # Create
    candidate = Candidate(
        site_id=current_user.site_id,
        entered_by=current_user.user_id,
        owner=current_user.user_id
    )

    candidate_schema.load(data, instance=candidate, partial=True)

    db.session.add(candidate)
    db.session.commit()

    return jsonify(candidate_schema.dump(candidate)), 201

@api_bp.route('/candidates/<int:id>', methods=['PUT'])
@login_required
@permission_required('candidates.edit')
def update_candidate(id):
    """Update candidate"""
    candidate = Candidate.query_for_site(current_user.site_id).get_or_404(id)
    data = request.get_json()

    # Validate
    errors = candidate_schema.validate(data, partial=True)
    if errors:
        return jsonify({'errors': errors}), 400

    # Update
    candidate_schema.load(data, instance=candidate, partial=True)
    candidate.date_modified = datetime.utcnow()

    db.session.commit()

    return jsonify(candidate_schema.dump(candidate))

@api_bp.route('/candidates/<int:id>', methods=['DELETE'])
@login_required
@permission_required('candidates.delete')
def delete_candidate(id):
    """Delete candidate"""
    candidate = Candidate.query_for_site(current_user.site_id).get_or_404(id)
    candidate.is_admin_hidden = True

    db.session.commit()

    return '', 204

# Autocomplete endpoint
@api_bp.route('/candidates/autocomplete')
@login_required
def autocomplete_candidates():
    """Autocomplete candidate names"""
    query = request.args.get('q', '')
    max_results = request.args.get('max', 10, type=int)

    candidates = Candidate.query_for_site(current_user.site_id).filter(
        db.or_(
            Candidate.first_name.like(f'{query}%'),
            Candidate.last_name.like(f'{query}%')
        )
    ).limit(max_results).all()

    return jsonify([
        {
            'id': c.candidate_id,
            'name': c.full_name,
            'email': c.email1
        }
        for c in candidates
    ])
```

**Marshmallow Schemas:**
```python
# app/api/schemas.py
from marshmallow import Schema, fields, validate

class CandidateSchema(Schema):
    candidate_id = fields.Int(dump_only=True)
    site_id = fields.Int(dump_only=True)
    first_name = fields.Str(required=True, validate=validate.Length(max=50))
    last_name = fields.Str(required=True, validate=validate.Length(max=50))
    email1 = fields.Email()
    email2 = fields.Email()
    phone_home = fields.Str()
    phone_cell = fields.Str()
    phone_work = fields.Str()
    address = fields.Str()
    city = fields.Str()
    state = fields.Str()
    zip = fields.Str()
    key_skills = fields.Str()
    current_employer = fields.Str()
    is_hot = fields.Boolean()
    can_relocate = fields.Boolean()
    notes = fields.Str()
    date_created = fields.DateTime(dump_only=True)
    date_modified = fields.DateTime(dump_only=True)

    # Nested relationships
    pipeline_entries = fields.Nested('PipelineEntrySchema', many=True, dump_only=True)
    attachments = fields.Nested('AttachmentSchema', many=True, dump_only=True)

class JobOrderSchema(Schema):
    joborder_id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    description = fields.Str()
    company_id = fields.Int(required=True)
    contact_id = fields.Int()
    status = fields.Int()
    openings = fields.Int()
    openings_available = fields.Int()
    # ... more fields
```

**API Documentation (OpenAPI/Swagger):**
```python
# Install: pip install flask-swagger-ui flasgger

from flasgger import Swagger

swagger = Swagger(app, template={
    "swagger": "2.0",
    "info": {
        "title": "OpenCATS API",
        "description": "Applicant Tracking System REST API",
        "version": "1.0.0"
    },
    "basePath": "/api/v1",
    "schemes": ["http", "https"]
})

# In view docstrings:
@api_bp.route('/candidates/<int:id>')
def get_candidate(id):
    """
    Get candidate by ID
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Candidate details
        schema:
          $ref: '#/definitions/Candidate'
      404:
        description: Candidate not found
    """
    pass
```

---

## 6. UI & Frontend

### 6.1 Current Frontend (PHP)

**Template System:** Custom PHP-based (NOT Smarty)
**JavaScript:** jQuery 1.3.2 + custom libraries
**CSS:** Custom CSS, table-based layouts
**Responsive:** No (desktop-only)

**JavaScript Libraries:**
- `jquery-1.3.2.min.js` - jQuery framework
- `lib.js` - Core utilities (28KB)
- `calendarDateInput.js` - Date picker (41KB)
- `dataGrid.js` - Table resizing/sorting (24KB)
- `suggest.js` - Autocomplete (18KB)
- `submodal/subModal.js` - Modal popups (10KB)

**UI Components:**
- Data grids with sorting/filtering/pagination
- Modal popups (DHTML-based)
- Calendar/date pickers
- Autocomplete fields
- List editors (single/dual-pane)

### 6.2 Proposed Frontend (Flask)

**Template Engine:** Jinja2 (built into Flask)
**CSS Framework:** Bootstrap 5 or Tailwind CSS
**JavaScript:** Modern ES6+ with Vue.js or Alpine.js
**Build Tool:** Webpack or Vite
**Responsive:** Mobile-first design

**Template Structure:**
```html
<!-- app/templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}OpenCATS{% endblock %}</title>

    <!-- CSS -->
    <link href="{{ url_for('static', filename='css/bootstrap.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static', filename='css/main.css') }}" rel="stylesheet">
    {% block styles %}{% endblock %}
</head>
<body>
    {% include 'components/navbar.html' %}

    <div class="container-fluid">
        <div class="row">
            {% include 'components/sidebar.html' %}

            <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}

                {% block content %}{% endblock %}
            </main>
        </div>
    </div>

    {% include 'components/footer.html' %}

    <!-- JavaScript -->
    <script src="{{ url_for('static', filename='js/bootstrap.bundle.min.js') }}"></script>
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>

<!-- app/templates/candidates/show.html -->
{% extends "base.html" %}

{% block title %}{{ candidate.full_name }} - Candidates{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>{{ candidate.full_name }}</h1>
    <div>
        <a href="{{ url_for('candidates.edit', id=candidate.candidate_id) }}" class="btn btn-primary">Edit</a>
        <button class="btn btn-danger" onclick="deleteCandidate({{ candidate.candidate_id }})">Delete</button>
    </div>
</div>

<div class="row">
    <div class="col-md-8">
        <div class="card mb-3">
            <div class="card-header">
                <h5>Contact Information</h5>
            </div>
            <div class="card-body">
                <dl class="row">
                    <dt class="col-sm-3">Email:</dt>
                    <dd class="col-sm-9">{{ candidate.email1 }}</dd>

                    <dt class="col-sm-3">Phone:</dt>
                    <dd class="col-sm-9">{{ candidate.phone_cell }}</dd>

                    <dt class="col-sm-3">Location:</dt>
                    <dd class="col-sm-9">{{ candidate.city }}, {{ candidate.state }}</dd>
                </dl>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h5>Pipeline Entries</h5>
            </div>
            <div class="card-body">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Job Order</th>
                            <th>Status</th>
                            <th>Rating</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for entry in pipeline_entries %}
                        <tr>
                            <td><a href="{{ url_for('joborders.show', id=entry.joborder_id) }}">{{ entry.joborder.title }}</a></td>
                            <td>{{ entry.status_obj.short_description }}</td>
                            <td>{% include 'components/rating.html' %}</td>
                            <td>{{ entry.date_created.strftime('%Y-%m-%d') }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="col-md-4">
        <div class="card">
            <div class="card-header">
                <h5>Attachments</h5>
            </div>
            <div class="card-body">
                <ul class="list-group">
                    {% for attachment in attachments %}
                    <li class="list-group-item">
                        <a href="{{ url_for('attachments.download', id=attachment.attachment_id) }}">
                            {{ attachment.original_filename }}
                        </a>
                    </li>
                    {% endfor %}
                </ul>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**Modern JavaScript (ES6+):**
```javascript
// app/static/js/candidates.js
class CandidateManager {
    constructor() {
        this.initEventListeners();
    }

    initEventListeners() {
        // Autocomplete
        document.querySelectorAll('[data-autocomplete]').forEach(input => {
            this.initAutocomplete(input);
        });

        // Form validation
        document.querySelectorAll('form[data-validate]').forEach(form => {
            form.addEventListener('submit', this.validateForm.bind(this));
        });
    }

    initAutocomplete(input) {
        let timeout = null;

        input.addEventListener('input', (e) => {
            clearTimeout(timeout);

            timeout = setTimeout(() => {
                this.fetchAutocomplete(input.value, input.dataset.autocomplete)
                    .then(results => this.displayAutocomplete(input, results));
            }, 300);
        });
    }

    async fetchAutocomplete(query, endpoint) {
        const response = await fetch(`/api/v1/${endpoint}?q=${encodeURIComponent(query)}`);
        return await response.json();
    }

    displayAutocomplete(input, results) {
        // Create dropdown with results
        let dropdown = document.querySelector('.autocomplete-dropdown');
        if (!dropdown) {
            dropdown = document.createElement('div');
            dropdown.className = 'autocomplete-dropdown';
            input.parentNode.appendChild(dropdown);
        }

        dropdown.innerHTML = results.map(item =>
            `<div class="autocomplete-item" data-id="${item.id}">${item.name}</div>`
        ).join('');

        dropdown.querySelectorAll('.autocomplete-item').forEach(item => {
            item.addEventListener('click', () => {
                input.value = item.textContent;
                input.dataset.selectedId = item.dataset.id;
                dropdown.innerHTML = '';
            });
        });
    }

    validateForm(e) {
        const form = e.target;
        let isValid = true;

        // Check required fields
        form.querySelectorAll('[required]').forEach(field => {
            if (!field.value.trim()) {
                this.showError(field, 'This field is required');
                isValid = false;
            }
        });

        if (!isValid) {
            e.preventDefault();
        }

        return isValid;
    }

    showError(field, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;

        field.classList.add('is-invalid');
        field.parentNode.appendChild(errorDiv);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    new CandidateManager();
});
```

**Vue.js Component Example:**
```vue
<!-- app/static/js/components/PipelineBoard.vue -->
<template>
  <div class="pipeline-board">
    <div v-for="status in statuses" :key="status.id" class="pipeline-column">
      <h3>{{ status.name }} ({{ getCandidatesInStatus(status.id).length }})</h3>

      <draggable
        v-model="getCandidatesInStatus(status.id)"
        :group="{ name: 'pipeline' }"
        @change="onStatusChange($event, status.id)"
        class="candidate-list">

        <div v-for="candidate in getCandidatesInStatus(status.id)"
             :key="candidate.id"
             class="candidate-card">
          <h5>{{ candidate.name }}</h5>
          <p>{{ candidate.email }}</p>
          <div class="rating">
            <star-rating :rating="candidate.rating" @update="updateRating"></star-rating>
          </div>
        </div>
      </draggable>
    </div>
  </div>
</template>

<script>
import draggable from 'vuedraggable';

export default {
  components: { draggable },

  props: {
    joborderId: Number
  },

  data() {
    return {
      statuses: [],
      candidates: []
    };
  },

  mounted() {
    this.loadPipeline();
  },

  methods: {
    async loadPipeline() {
      const response = await fetch(`/api/v1/joborders/${this.joborderId}/pipeline`);
      const data = await response.json();

      this.statuses = data.statuses;
      this.candidates = data.candidates;
    },

    getCandidatesInStatus(statusId) {
      return this.candidates.filter(c => c.status === statusId);
    },

    async onStatusChange(event, newStatus) {
      if (event.added) {
        const candidate = event.added.element;

        await fetch(`/api/v1/pipeline/${candidate.pipeline_id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: newStatus })
        });
      }
    }
  }
};
</script>
```

---

## 7. Migration Strategy

### 7.1 Database Migration

**Step 1: Schema Analysis**
- Export current schema: `mysqldump -d cats_dev > current_schema.sql`
- Document all tables, columns, indexes, relationships
- Identify data types, constraints, defaults

**Step 2: Create SQLAlchemy Models**
- Map each table to SQLAlchemy model
- Define relationships (ForeignKey, backref, lazy loading)
- Add model methods and properties
- Implement multi-tenancy filters

**Step 3: Data Migration**
```python
# migrations/migrate_data.py
from app import create_app, db
from app.models import Candidate, Company, JobOrder, User
import MySQLdb

def migrate_candidates():
    """Migrate candidates from old database"""
    # Connect to old database
    old_db = MySQLdb.connect(
        host='localhost',
        user='cats',
        passwd='password',
        db='cats_dev'
    )
    cursor = old_db.cursor(MySQLdb.cursors.DictCursor)

    # Fetch all candidates
    cursor.execute("SELECT * FROM candidate WHERE is_admin_hidden = 0")
    candidates = cursor.fetchall()

    # Create new records
    for row in candidates:
        candidate = Candidate(
            candidate_id=row['candidate_id'],
            site_id=row['site_id'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            email1=row['email1'],
            # ... map all fields
        )
        db.session.add(candidate)

    db.session.commit()
    print(f"Migrated {len(candidates)} candidates")

def migrate_all():
    """Run all migrations"""
    migrate_candidates()
    migrate_companies()
    migrate_joborders()
    migrate_users()
    # ... more entities

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        migrate_all()
```

**Step 4: Verify Migration**
- Compare record counts: `SELECT COUNT(*) FROM table`
- Verify relationships
- Test data integrity
- Run unit tests

### 7.2 Code Migration Approach

**Phase 1: Foundation (Months 1-2)**
- Set up Flask project structure
- Implement authentication system
- Create SQLAlchemy models
- Migrate database schema
- Set up testing framework

**Phase 2: Core Modules (Months 3-5)**
- Migrate Candidates module
- Migrate Job Orders module
- Migrate Companies module
- Migrate Contacts module
- Implement search functionality

**Phase 3: Supporting Features (Months 6-7)**
- Calendar/Activities module
- Email integration
- Document handling
- Reports module
- Import/Export

**Phase 4: Advanced Features (Months 8-9)**
- Career Portal
- Settings module
- Queue system
- Advanced search
- Custom fields

**Phase 5: Testing & Polish (Months 10-11)**
- Comprehensive testing
- Performance optimization
- Security audit
- UI/UX improvements
- Documentation

**Phase 6: Deployment (Month 12)**
- Production deployment
- Data migration
- User training
- Monitoring setup
- Rollback plan

### 7.3 Parallel Development Strategy

**Option 1: Big Bang (Not Recommended)**
- Complete rewrite before switching
- High risk, long timeline
- All-or-nothing deployment

**Option 2: Incremental Migration (Recommended)**
- Run PHP and Flask side-by-side
- Migrate module by module
- Share database
- Gradual cutover

**Implementation:**
```
Phase 1: Setup
- Flask app runs on /new/ path
- PHP app remains on /
- Shared database (read-only for Flask initially)

Phase 2: Read-Only Flask
- Migrate view pages (show, list)
- Link from PHP to Flask views
- Verify data display

Phase 3: Write Operations
- Migrate forms (add, edit)
- Write to shared database
- Maintain data integrity

Phase 4: Complete Migration
- All modules in Flask
- Retire PHP codebase
- Full Flask deployment
```

### 7.4 Testing Strategy

**Unit Tests:**
```python
# tests/unit/test_candidates.py
import pytest
from app.models import Candidate

def test_candidate_creation(db_session):
    """Test creating a candidate"""
    candidate = Candidate(
        site_id=1,
        first_name='John',
        last_name='Doe',
        email1='john@example.com'
    )

    db_session.add(candidate)
    db_session.commit()

    assert candidate.candidate_id is not None
    assert candidate.full_name == 'John Doe'

def test_candidate_search(db_session, sample_candidates):
    """Test candidate search"""
    results = Candidate.query.filter(
        Candidate.first_name.like('John%')
    ).all()

    assert len(results) > 0
```

**Integration Tests:**
```python
# tests/integration/test_candidates_api.py
def test_create_candidate_api(client, auth_headers):
    """Test creating candidate via API"""
    data = {
        'first_name': 'Jane',
        'last_name': 'Smith',
        'email1': 'jane@example.com'
    }

    response = client.post('/api/v1/candidates',
                          json=data,
                          headers=auth_headers)

    assert response.status_code == 201
    assert response.json['first_name'] == 'Jane'

def test_get_candidates_pagination(client, auth_headers):
    """Test candidate list with pagination"""
    response = client.get('/api/v1/candidates?page=1&per_page=10',
                         headers=auth_headers)

    assert response.status_code == 200
    assert 'candidates' in response.json
    assert len(response.json['candidates']) <= 10
```

**End-to-End Tests:**
```python
# tests/e2e/test_candidate_workflow.py
from selenium import webdriver

def test_add_candidate_workflow(browser):
    """Test complete add candidate workflow"""
    # Login
    browser.get('http://localhost:5000/login')
    browser.find_element_by_id('username').send_keys('admin')
    browser.find_element_by_id('password').send_keys('password')
    browser.find_element_by_id('submit').click()

    # Navigate to add candidate
    browser.get('http://localhost:5000/candidates/add')

    # Fill form
    browser.find_element_by_id('first_name').send_keys('John')
    browser.find_element_by_id('last_name').send_keys('Doe')
    browser.find_element_by_id('email1').send_keys('john@example.com')

    # Submit
    browser.find_element_by_id('submit').click()

    # Verify success
    assert 'Candidate John Doe added successfully' in browser.page_source
```

---

## 8. Technology Stack Recommendations

### 8.1 Backend

**Core Framework:**
- **Flask 3.0+** - Lightweight, flexible, well-documented
- **Alternatives:** Django (more batteries-included), FastAPI (async, API-focused)

**Extensions:**
- **Flask-SQLAlchemy 3.0+** - Database ORM
- **Flask-Login** - User session management
- **Flask-WTF** - Form handling and CSRF protection
- **Flask-Mail** - Email sending
- **Flask-Migrate** - Alembic database migrations
- **Flask-CORS** - Cross-Origin Resource Sharing
- **Flask-Limiter** - Rate limiting
- **Marshmallow** - Object serialization/deserialization
- **Celery** - Async task queue
- **Redis** - Caching and session storage

**Database:**
- **MySQL 8.0+** or **MariaDB 10.6+** (maintain compatibility)
- **Alembic** for migrations

**Search:**
- **Elasticsearch 8.x** - Full-text search (upgrade from Sphinx)
- **Alternative:** PostgreSQL with Full-Text Search

**File Storage:**
- Local filesystem (development)
- **S3-compatible storage** (production) - AWS S3, MinIO, etc.

**Resume Parsing:**
- **PyPDF2** or **pdfplumber** - PDF text extraction
- **python-docx** - Word document parsing
- **textract** - Universal text extraction

### 8.2 Frontend

**CSS Framework:**
- **Bootstrap 5.3+** - Comprehensive, responsive, well-supported
- **Alternative:** Tailwind CSS (utility-first)

**JavaScript:**
- **ES6+ (vanilla)** - For simple interactions
- **Vue.js 3** or **Alpine.js** - For reactive components
- **Axios** - HTTP client

**Build Tools:**
- **Vite** - Fast build tool
- **Alternative:** Webpack

**UI Components:**
- **DataTables** - Feature-rich tables
- **Select2** - Enhanced select boxes
- **Flatpickr** - Modern date picker
- **SortableJS** - Drag-and-drop

### 8.3 Development Tools

**Code Quality:**
- **Black** - Code formatter
- **Flake8** - Linter
- **mypy** - Type checker
- **pre-commit** - Git hooks

**Testing:**
- **pytest** - Test framework
- **pytest-cov** - Coverage reporting
- **pytest-flask** - Flask testing utilities
- **Selenium** - E2E testing
- **Factory Boy** - Test fixtures

**Documentation:**
- **Sphinx** - Documentation generator
- **MkDocs** - Markdown documentation
- **Swagger/OpenAPI** - API documentation

**Deployment:**
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Gunicorn** - WSGI server
- **Nginx** - Reverse proxy
- **Supervisor** - Process management

**Monitoring:**
- **Sentry** - Error tracking
- **Prometheus + Grafana** - Metrics and monitoring
- **ELK Stack** - Log aggregation

### 8.4 Configuration Management

```python
# config.py
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://cats:password@localhost/cats_dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Session
    SESSION_TYPE = 'redis'
    SESSION_REDIS = os.environ.get('REDIS_URL') or 'redis://localhost:6379'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'localhost'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@opencats.org'

    # File uploads
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'rtf', 'txt', 'odt'}

    # Celery
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'

    # Elasticsearch
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL') or 'http://localhost:9200'

    # Security
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://cats:password@localhost/cats_test'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
```

---

## 9. Implementation Roadmap

### Month 1: Project Setup & Foundation
**Week 1-2:**
- Initialize Flask project structure
- Set up version control (Git)
- Configure development environment
- Set up CI/CD pipeline
- Create initial documentation

**Week 3-4:**
- Create SQLAlchemy models for core entities
- Set up Alembic migrations
- Implement authentication system
- Create base templates
- Set up testing framework

**Deliverables:**
- Working Flask application skeleton
- User authentication working
- Database models defined
- Test suite initialized

### Month 2: Core Infrastructure
**Week 1-2:**
- Implement permission system
- Create base CRUD operations
- Set up API blueprint structure
- Implement session management
- Configure email system

**Week 3-4:**
- Create reusable UI components
- Implement data grid component
- Set up file upload handling
- Create form validation utilities
- Implement search infrastructure

**Deliverables:**
- Complete authentication/authorization
- Reusable components library
- Working file upload system
- Basic API endpoints

### Month 3: Candidates Module
**Week 1:**
- Candidate model finalization
- Candidate list view
- Candidate detail view
- Basic search functionality

**Week 2:**
- Candidate add form
- Candidate edit form
- Form validation
- Duplicate detection

**Week 3:**
- Resume upload
- Resume parsing
- Text extraction
- Auto-populate fields

**Week 4:**
- Candidate API endpoints
- Testing and bug fixes
- Documentation
- Performance optimization

**Deliverables:**
- Complete Candidates module
- API endpoints working
- Resume parsing functional
- Comprehensive tests

### Month 4: Job Orders Module
**Week 1:**
- JobOrder model
- Job list view
- Job detail view
- Job search

**Week 2:**
- Job add/edit forms
- Company/contact linking
- Status management
- Openings tracking

**Week 3:**
- Pipeline implementation
- Add candidate to pipeline
- Status workflow
- Rating system

**Week 4:**
- Pipeline visualization
- Drag-and-drop interface (if using Vue.js)
- API endpoints
- Testing

**Deliverables:**
- Complete JobOrders module
- Working pipeline system
- Drag-and-drop interface
- API integration

### Month 5: Companies & Contacts
**Week 1-2:**
- Company module (CRUD)
- Department management
- Company search
- Company API

**Week 3-4:**
- Contact module (CRUD)
- Contact linking
- Cold call list
- Contact API

**Deliverables:**
- Companies module complete
- Contacts module complete
- Relationship management working

### Month 6: Search & Filtering
**Week 1-2:**
- Elasticsearch integration
- Index creation
- Full-text search implementation
- Search API

**Week 3-4:**
- Advanced search UI
- Saved searches
- Search filters
- Autocomplete improvements

**Deliverables:**
- Full-text search working
- Advanced search UI
- Saved searches functional

### Month 7: Calendar & Activities
**Week 1-2:**
- Calendar event model
- Calendar view
- Event creation/editing
- Reminder system

**Week 3-4:**
- Activity logging
- Activity types
- Activity history
- Email integration

**Deliverables:**
- Calendar module complete
- Activity logging working
- Email notifications functional

### Month 8: Reports & Analytics
**Week 1-2:**
- Dashboard statistics
- Basic reports (candidates, jobs, placements)
- Report generation
- Export functionality

**Week 3-4:**
- Advanced reports
- Custom date ranges
- EEO reports
- Charts and visualizations

**Deliverables:**
- Reports module complete
- Dashboard with statistics
- Export functionality

### Month 9: Import/Export & Career Portal
**Week 1-2:**
- Import wizard
- CSV import (candidates, companies)
- Bulk resume import
- Data validation

**Week 3-4:**
- Career portal setup
- Job listing page
- Application form
- Questionnaire system

**Deliverables:**
- Import/export working
- Career portal functional

### Month 10: Settings & Admin
**Week 1-2:**
- Settings module
- User management
- Email templates
- Site configuration

**Week 3-4:**
- Custom fields
- Backup/restore
- System settings
- Multi-tenancy admin

**Deliverables:**
- Settings module complete
- Admin functionality working

### Month 11: Testing & Optimization
**Week 1-2:**
- Comprehensive testing (unit, integration, E2E)
- Bug fixes
- Performance optimization
- Security audit

**Week 3-4:**
- UI/UX improvements
- Accessibility audit
- Cross-browser testing
- Mobile responsiveness

**Deliverables:**
- 90%+ test coverage
- Performance optimized
- Security hardened
- Responsive design

### Month 12: Deployment & Launch
**Week 1-2:**
- Production environment setup
- Data migration execution
- Smoke testing
- Monitoring setup

**Week 3:**
- User training
- Documentation finalization
- Soft launch (limited users)
- Feedback collection

**Week 4:**
- Full launch
- Post-launch support
- Bug fixes
- Performance monitoring

**Deliverables:**
- Production deployment complete
- Data migrated successfully
- Users trained
- Documentation complete

---

## 10. Success Metrics

### Performance Metrics
- **Page Load Time:** < 2 seconds (95th percentile)
- **API Response Time:** < 500ms (95th percentile)
- **Database Query Time:** < 100ms average
- **Search Response Time:** < 1 second

### Quality Metrics
- **Test Coverage:** > 90%
- **Code Quality:** A grade (SonarQube)
- **Security:** No critical vulnerabilities
- **Accessibility:** WCAG 2.1 AA compliant

### User Metrics
- **User Adoption:** 100% within 3 months
- **User Satisfaction:** > 4.0/5.0
- **Bug Reports:** < 10 critical bugs per month
- **Support Tickets:** < 20% increase from baseline

### Business Metrics
- **Data Migration Success:** 100% data integrity
- **Downtime:** < 1 hour during migration
- **Training Time:** < 4 hours per user
- **ROI:** Positive within 12 months

---

## Conclusion

This specification provides a comprehensive blueprint for rewriting OpenCATS from PHP to Python Flask. The migration will modernize the codebase, improve security, enhance performance, and provide a better user experience while preserving all existing functionality.

Key benefits of the Flask rewrite:
- **Modern technology stack** with active community support
- **Improved security** with bcrypt password hashing and CSRF protection
- **Better performance** with optimized queries and caching
- **RESTful API** for third-party integrations
- **Responsive design** for mobile access
- **Comprehensive testing** for reliability
- **Better maintainability** with clean code architecture

The 12-month timeline provides realistic estimates for a complete migration with thorough testing and quality assurance. The incremental migration approach minimizes risk and allows for continuous operation during the transition.
