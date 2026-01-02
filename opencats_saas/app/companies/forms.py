"""
Company Forms
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, URL


class CompanyForm(FlaskForm):
    """Company add/edit form"""
    # Basic Information
    name = StringField('Company Name', validators=[DataRequired(), Length(max=255)])

    # Contact Information
    phone1 = StringField('Phone', validators=[Optional(), Length(max=40)])
    phone2 = StringField('Alt Phone', validators=[Optional(), Length(max=40)])
    fax = StringField('Fax', validators=[Optional(), Length(max=40)])
    url = StringField('Website', validators=[Optional(), URL(), Length(max=255)])

    # Address
    address = TextAreaField('Address', validators=[Optional()])
    city = StringField('City', validators=[Optional(), Length(max=64)])
    state = StringField('State', validators=[Optional(), Length(max=64)])
    zip = StringField('ZIP Code', validators=[Optional(), Length(max=16)])
    country = StringField('Country', validators=[Optional(), Length(max=64)])

    # Details
    key_technologies = TextAreaField('Key Technologies', validators=[Optional()],
                                    description='Technologies this company uses or needs')
    notes = TextAreaField('Notes', validators=[Optional()])

    # Flags
    is_hot = BooleanField('Hot Client')

    submit = SubmitField('Save Company')


class CompanySearchForm(FlaskForm):
    """Company search form"""
    name = StringField('Company Name', validators=[Optional()])
    city = StringField('City', validators=[Optional()])
    state = StringField('State', validators=[Optional()])
    technologies = StringField('Technologies', validators=[Optional()])

    hot_only = BooleanField('Hot Clients Only')

    submit = SubmitField('Search')


class DepartmentForm(FlaskForm):
    """Department form"""
    name = StringField('Department Name', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Add Department')
