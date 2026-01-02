"""
API Schemas - Marshmallow Serialization
"""
from marshmallow import Schema, fields, validate, validates, ValidationError
from datetime import datetime


class UserSchema(Schema):
    """User serialization"""
    user_id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    email = fields.Email()
    first_name = fields.Str()
    last_name = fields.Str()
    access_level = fields.Int()
    is_active = fields.Bool()
    last_activity = fields.DateTime()
    date_created = fields.DateTime(dump_only=True)


class CandidateSchema(Schema):
    """Candidate serialization"""
    candidate_id = fields.Int(dump_only=True)
    first_name = fields.Str(required=True, validate=validate.Length(max=50))
    middle_name = fields.Str(validate=validate.Length(max=50))
    last_name = fields.Str(required=True, validate=validate.Length(max=50))

    # Contact
    email1 = fields.Email()
    email2 = fields.Email()
    phone_home = fields.Str(validate=validate.Length(max=40))
    phone_cell = fields.Str(validate=validate.Length(max=40))
    phone_work = fields.Str(validate=validate.Length(max=40))

    # Address
    address = fields.Str()
    city = fields.Str(validate=validate.Length(max=64))
    state = fields.Str(validate=validate.Length(max=64))
    zip = fields.Str(validate=validate.Length(max=16))

    # Professional
    key_skills = fields.Str()
    current_employer = fields.Str(validate=validate.Length(max=255))
    current_pay = fields.Str(validate=validate.Length(max=64))
    desired_pay = fields.Str(validate=validate.Length(max=64))

    # Flags
    is_hot = fields.Bool()
    is_active = fields.Bool()
    is_admin_hidden = fields.Bool()

    # Metadata
    source = fields.Str()
    owner = fields.Int()
    date_created = fields.DateTime(dump_only=True)
    date_modified = fields.DateTime(dump_only=True)

    # Nested
    attachments = fields.List(fields.Nested('AttachmentSchema'), dump_only=True)
    activities = fields.List(fields.Nested('ActivitySchema'), dump_only=True)


class JobOrderSchema(Schema):
    """Job order serialization"""
    joborder_id = fields.Int(dump_only=True)
    company_id = fields.Int(required=True)
    company_name = fields.Str(dump_only=True)
    contact_id = fields.Int()
    contact_name = fields.Str(dump_only=True)

    # Job details
    title = fields.Str(required=True, validate=validate.Length(max=255))
    type = fields.Int()  # Full-time, Contract, etc.
    duration = fields.Str(validate=validate.Length(max=64))
    rate_max = fields.Str(validate=validate.Length(max=64))
    salary = fields.Str(validate=validate.Length(max=64))

    # Requirements
    description = fields.Str()
    notes = fields.Str()

    # Status
    status = fields.Int()  # 0=Active, 1=On Hold, 2=Closed, 3=Canceled, 4=Filled
    openings = fields.Int()
    openings_available = fields.Int()

    # Flags
    is_hot = fields.Bool()
    public = fields.Bool()

    # Location
    city = fields.Str(validate=validate.Length(max=64))
    state = fields.Str(validate=validate.Length(max=64))

    # Metadata
    recruiter = fields.Int()
    owner = fields.Int()
    start_date = fields.Date()
    date_created = fields.DateTime(dump_only=True)
    date_modified = fields.DateTime(dump_only=True)

    # Pipeline
    pipeline = fields.List(fields.Nested('PipelineEntrySchema'), dump_only=True)


class CompanySchema(Schema):
    """Company serialization"""
    company_id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(max=255))

    # Contact
    phone1 = fields.Str(validate=validate.Length(max=40))
    phone2 = fields.Str(validate=validate.Length(max=40))
    fax = fields.Str(validate=validate.Length(max=40))
    url = fields.Url()

    # Address
    address = fields.Str()
    city = fields.Str(validate=validate.Length(max=64))
    state = fields.Str(validate=validate.Length(max=64))
    zip = fields.Str(validate=validate.Length(max=16))
    country = fields.Str(validate=validate.Length(max=64))

    # Details
    key_technologies = fields.Str()
    notes = fields.Str()

    # Flags
    is_hot = fields.Bool()
    is_active = fields.Bool()

    # Metadata
    owner = fields.Int()
    date_created = fields.DateTime(dump_only=True)
    date_modified = fields.DateTime(dump_only=True)

    # Relationships
    contacts = fields.List(fields.Nested('ContactSchema'), dump_only=True)
    job_orders = fields.List(fields.Nested('JobOrderSchema'), dump_only=True)


class ContactSchema(Schema):
    """Contact serialization"""
    contact_id = fields.Int(dump_only=True)
    company_id = fields.Int(required=True)
    company_name = fields.Str(dump_only=True)

    # Personal
    first_name = fields.Str(required=True, validate=validate.Length(max=50))
    last_name = fields.Str(required=True, validate=validate.Length(max=50))
    title = fields.Str(validate=validate.Length(max=128))

    # Contact
    email1 = fields.Email()
    email2 = fields.Email()
    phone_work = fields.Str(validate=validate.Length(max=40))
    phone_cell = fields.Str(validate=validate.Length(max=40))
    phone_other = fields.Str(validate=validate.Length(max=40))

    # Address
    address = fields.Str()
    city = fields.Str(validate=validate.Length(max=64))
    state = fields.Str(validate=validate.Length(max=64))
    zip = fields.Str(validate=validate.Length(max=16))

    # Flags
    is_hot = fields.Bool()
    left_company = fields.Bool()

    # Metadata
    owner = fields.Int()
    date_created = fields.DateTime(dump_only=True)
    date_modified = fields.DateTime(dump_only=True)


class PipelineEntrySchema(Schema):
    """Candidate-Job pipeline entry"""
    candidate_joborder_id = fields.Int(dump_only=True)
    candidate_id = fields.Int(required=True)
    candidate_name = fields.Str(dump_only=True)
    joborder_id = fields.Int(required=True)
    job_title = fields.Str(dump_only=True)

    status = fields.Int()
    rating_value = fields.Int()

    date_created = fields.DateTime(dump_only=True)
    date_modified = fields.DateTime(dump_only=True)


class AttachmentSchema(Schema):
    """File attachment"""
    attachment_id = fields.Int(dump_only=True)
    title = fields.Str()
    original_filename = fields.Str()
    stored_filename = fields.Str(dump_only=True)
    file_size = fields.Int(dump_only=True)
    text = fields.Str(dump_only=True)
    date_created = fields.DateTime(dump_only=True)


class ActivitySchema(Schema):
    """Activity log entry"""
    activity_id = fields.Int(dump_only=True)
    data_item_id = fields.Int()
    data_item_type = fields.Int()
    type = fields.Int()
    notes = fields.Str()
    entered_by = fields.Int()
    date_created = fields.DateTime(dump_only=True)


class ErrorSchema(Schema):
    """Error response"""
    error = fields.Str(required=True)
    message = fields.Str()
    field = fields.Str()


class PaginationSchema(Schema):
    """Pagination metadata"""
    page = fields.Int()
    per_page = fields.Int()
    total = fields.Int()
    pages = fields.Int()
    has_next = fields.Bool()
    has_prev = fields.Bool()


# Schema instances for reuse
user_schema = UserSchema()
users_schema = UserSchema(many=True)

candidate_schema = CandidateSchema()
candidates_schema = CandidateSchema(many=True)

joborder_schema = JobOrderSchema()
joborders_schema = JobOrderSchema(many=True)

company_schema = CompanySchema()
companies_schema = CompanySchema(many=True)

contact_schema = ContactSchema()
contacts_schema = ContactSchema(many=True)

pipeline_entry_schema = PipelineEntrySchema()
pipeline_entries_schema = PipelineEntrySchema(many=True)

attachment_schema = AttachmentSchema()
attachments_schema = AttachmentSchema(many=True)

activity_schema = ActivitySchema()
activities_schema = ActivitySchema(many=True)
