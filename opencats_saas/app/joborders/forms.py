"""
Job Order Forms
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, DateField, BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Optional, Length, NumberRange


class JobOrderForm(FlaskForm):
    """Job order add/edit form"""
    # Basic Information
    title = StringField('Job Title', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Job Description', validators=[Optional()])
    notes = TextAreaField('Internal Notes', validators=[Optional()])

    # Company & Contact
    company_id = SelectField('Company', coerce=int, validators=[DataRequired()])
    contact_id = SelectField('Contact', coerce=int, validators=[Optional()])
    company_department_id = SelectField('Department', coerce=int, validators=[Optional()])

    # Job Details
    type = SelectField('Job Type', coerce=int, choices=[
        (1, 'Permanent'),
        (2, 'Contract'),
        (3, 'Temporary'),
        (4, 'Contract to Hire'),
        (5, 'Freelance')
    ], validators=[DataRequired()])

    duration = StringField('Duration', validators=[Optional(), Length(max=64)])
    salary = StringField('Salary Range', validators=[Optional(), Length(max=64)])
    rate_max = StringField('Maximum Rate', validators=[Optional(), Length(max=64)])

    # Location
    city = StringField('City', validators=[Optional(), Length(max=64)])
    state = StringField('State', validators=[Optional(), Length(max=64)])

    # Status & Openings
    status = SelectField('Status', coerce=int, choices=[
        (1, 'Active'),
        (2, 'On Hold'),
        (3, 'Closed'),
        (4, 'Filled')
    ], default=1, validators=[DataRequired()])

    openings = IntegerField('Number of Openings',
                           validators=[DataRequired(), NumberRange(min=1, max=100)],
                           default=1)

    # Dates
    start_date = DateField('Start Date', validators=[Optional()], format='%Y-%m-%d')

    # Flags
    is_hot = BooleanField('Hot Job')
    public = BooleanField('Show on Career Portal')

    # Assignment
    recruiter = SelectField('Assigned Recruiter', coerce=int, validators=[Optional()])

    submit = SubmitField('Save Job Order')


class JobOrderSearchForm(FlaskForm):
    """Job order search form"""
    title = StringField('Job Title', validators=[Optional()])
    company_id = SelectField('Company', coerce=int, validators=[Optional()])

    status = SelectField('Status', coerce=int, choices=[
        (None, 'All'),
        (1, 'Active'),
        (2, 'On Hold'),
        (3, 'Closed'),
        (4, 'Filled')
    ], validators=[Optional()])

    type = SelectField('Job Type', coerce=int, choices=[
        (None, 'All'),
        (1, 'Permanent'),
        (2, 'Contract'),
        (3, 'Temporary'),
        (4, 'Contract to Hire'),
        (5, 'Freelance')
    ], validators=[Optional()])

    city = StringField('City', validators=[Optional()])
    state = StringField('State', validators=[Optional()])

    hot_only = BooleanField('Hot Jobs Only')

    submit = SubmitField('Search')


class AddToPipelineForm(FlaskForm):
    """Add candidate to pipeline form"""
    candidate_id = HiddenField('Candidate ID', validators=[DataRequired()])
    submit = SubmitField('Add to Pipeline')
