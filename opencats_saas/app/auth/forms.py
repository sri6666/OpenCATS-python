"""
Authentication Forms
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp, ValidationError
from app.models import Site, User
import re


class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class TenantRegistrationForm(FlaskForm):
    """Tenant/organization signup form"""
    # Company info
    company_name = StringField('Company Name', validators=[
        DataRequired(),
        Length(min=2, max=128)
    ])
    subdomain = StringField('Subdomain', validators=[
        DataRequired(),
        Length(min=3, max=64),
        Regexp(r'^[a-z0-9-]+$', message='Subdomain can only contain lowercase letters, numbers, and hyphens')
    ], description='yourcompany.opencats.app')

    # Admin user info
    first_name = StringField('First Name', validators=[
        DataRequired(),
        Length(min=2, max=50)
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(),
        Length(min=2, max=50)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscores')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])

    # Terms acceptance
    accept_terms = BooleanField('I accept the Terms of Service and Privacy Policy', validators=[
        DataRequired()
    ])

    submit = SubmitField('Start Free Trial')

    def validate_subdomain(self, field):
        """Check if subdomain is available"""
        # Reserved subdomains
        reserved = ['www', 'api', 'admin', 'app', 'mail', 'smtp', 'ftp', 'blog',
                   'help', 'support', 'status', 'dev', 'staging', 'test']

        if field.data.lower() in reserved:
            raise ValidationError('This subdomain is reserved. Please choose another.')

        # Check database
        if Site.query.filter_by(subdomain=field.data.lower()).first():
            raise ValidationError('This subdomain is already taken. Please choose another.')

    def validate_email(self, field):
        """Check if email is already registered"""
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('This email is already registered. Please log in or use a different email.')

    def validate_username(self, field):
        """Check if username is available"""
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('This username is already taken. Please choose another.')

    def validate_password(self, field):
        """Enforce password complexity"""
        password = field.data

        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')

        # Check for at least one uppercase, one lowercase, one digit
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter.')

        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter.')

        if not re.search(r'\d', password):
            raise ValidationError('Password must contain at least one number.')


class SignupForm(FlaskForm):
    """User signup form (for adding users to existing tenant)"""
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8)
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password')
    ])
    submit = SubmitField('Create Account')


class ForgotPasswordForm(FlaskForm):
    """Request password reset form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    """Reset password form"""
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8)
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password')
    ])
    submit = SubmitField('Reset Password')


class ChangePasswordForm(FlaskForm):
    """Change password form (for logged-in users)"""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8)
    ])
    new_password_confirm = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password')
    ])
    submit = SubmitField('Change Password')
