"""
Contact Forms
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length


class ContactForm(FlaskForm):
    """Contact add/edit form"""
    # Company
    company_id = SelectField('Company', coerce=int, validators=[DataRequired()])
    company_department_id = SelectField('Department', coerce=int, validators=[Optional()])

    # Personal Information
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    title = StringField('Job Title', validators=[Optional(), Length(max=128)])

    # Contact Information
    email1 = StringField('Primary Email', validators=[Optional(), Email()])
    email2 = StringField('Secondary Email', validators=[Optional(), Email()])
    phone_work = StringField('Work Phone', validators=[Optional(), Length(max=40)])
    phone_cell = StringField('Cell Phone', validators=[Optional(), Length(max=40)])
    phone_other = StringField('Other Phone', validators=[Optional(), Length(max=40)])

    # Address
    address = TextAreaField('Address', validators=[Optional()])
    city = StringField('City', validators=[Optional(), Length(max=64)])
    state = StringField('State', validators=[Optional(), Length(max=64)])
    zip = StringField('ZIP Code', validators=[Optional(), Length(max=16)])

    # Details
    notes = TextAreaField('Notes', validators=[Optional()])

    # Flags
    is_hot = BooleanField('Hot Contact')
    left_company = BooleanField('No Longer at Company')

    # Hierarchy
    reports_to = SelectField('Reports To', coerce=int, validators=[Optional()])

    submit = SubmitField('Save Contact')


class ContactSearchForm(FlaskForm):
    """Contact search form"""
    name = StringField('Name', validators=[Optional()])
    email = StringField('Email', validators=[Optional()])
    company_id = SelectField('Company', coerce=int, validators=[Optional()])
    title = StringField('Job Title', validators=[Optional()])

    hot_only = BooleanField('Hot Contacts Only')

    submit = SubmitField('Search')
