"""
Candidate Forms
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length


class CandidateForm(FlaskForm):
    """Candidate add/edit form"""
    # Personal Information
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    middle_name = StringField('Middle Name', validators=[Optional(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])

    # Contact Information
    email1 = StringField('Primary Email', validators=[DataRequired(), Email()])
    email2 = StringField('Secondary Email', validators=[Optional(), Email()])
    phone_home = StringField('Home Phone', validators=[Optional()])
    phone_cell = StringField('Cell Phone', validators=[Optional()])
    phone_work = StringField('Work Phone', validators=[Optional()])

    # Address
    address = TextAreaField('Address', validators=[Optional()])
    city = StringField('City', validators=[Optional(), Length(max=64)])
    state = StringField('State', validators=[Optional(), Length(max=64)])
    zip = StringField('ZIP Code', validators=[Optional(), Length(max=16)])
    country = StringField('Country', validators=[Optional(), Length(max=64)])

    # Professional Information
    source = StringField('Source', validators=[Optional(), Length(max=64)],
                        description='How did you find this candidate?')
    key_skills = TextAreaField('Key Skills', validators=[Optional()],
                              description='Comma-separated list of skills')
    current_employer = StringField('Current Employer', validators=[Optional(), Length(max=255)])
    current_pay = StringField('Current Salary/Rate', validators=[Optional(), Length(max=64)])
    desired_pay = StringField('Desired Salary/Rate', validators=[Optional(), Length(max=64)])
    date_available = StringField('Date Available', validators=[Optional(), Length(max=64)])

    # Flags
    is_hot = BooleanField('Hot Candidate')
    can_relocate = BooleanField('Can Relocate')

    # Notes
    notes = TextAreaField('Notes', validators=[Optional()])

    # EEO Information (optional)
    eeo_gender = SelectField('Gender', choices=[
        ('', 'Prefer not to say'),
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    ], validators=[Optional()])

    submit = SubmitField('Save Candidate')


class CandidateSearchForm(FlaskForm):
    """Advanced candidate search form"""
    name = StringField('Name', validators=[Optional()])
    email = StringField('Email', validators=[Optional()])
    phone = StringField('Phone', validators=[Optional()])
    skills = StringField('Skills', validators=[Optional()],
                        description='Search in key skills')
    city = StringField('City', validators=[Optional()])
    state = StringField('State', validators=[Optional()])
    source = StringField('Source', validators=[Optional()])

    hot_only = BooleanField('Hot Candidates Only')
    active_only = BooleanField('Active Only', default=True)

    submit = SubmitField('Search')


class ResumeUploadForm(FlaskForm):
    """Resume upload form"""
    resume = FileField('Resume', validators=[
        DataRequired(),
        FileAllowed(['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'], 'Resumes only!')
    ])
    submit = SubmitField('Upload Resume')
