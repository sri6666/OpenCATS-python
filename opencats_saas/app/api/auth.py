"""
API Authentication - JWT Token Management
"""
from flask import request, jsonify, current_app
from functools import wraps
import jwt
from datetime import datetime, timedelta
from app.api import api_bp
from app.models import User, Site
from app.extensions import db, limiter


def generate_token(user):
    """Generate JWT token for user"""
    payload = {
        'user_id': user.user_id,
        'site_id': user.site_id,
        'access_level': user.access_level,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }

    token = jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

    return token


def verify_token(token):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer TOKEN
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        # Verify token
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Token is invalid or expired'}), 401

        # Get user
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401

        # Check site is active
        site = Site.query.get(user.site_id)
        if not site or site.is_deleted or site.subscription_status in ['suspended', 'cancelled']:
            return jsonify({'error': 'Subscription inactive'}), 403

        return f(current_user=user, *args, **kwargs)

    return decorated


def api_key_required(f):
    """Decorator to require API key (Enterprise plan only)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401

        # Verify API key
        site = Site.query.filter_by(api_key=api_key, is_deleted=False).first()

        if not site:
            return jsonify({'error': 'Invalid API key'}), 401

        # Check plan allows API access
        if site.subscription_plan != 'enterprise':
            return jsonify({'error': 'API access requires Enterprise plan'}), 403

        if site.subscription_status not in ['active', 'trial']:
            return jsonify({'error': 'Subscription inactive'}), 403

        return f(site=site, *args, **kwargs)

    return decorated


@api_bp.route('/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """
    Authenticate and get JWT token

    POST /api/v1/auth/login
    {
        "username": "john@example.com",
        "password": "password123"
    }

    Returns:
    {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "expires_in": 86400,
        "user": {
            "user_id": 1,
            "username": "john@example.com",
            "access_level": 400
        }
    }
    """
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400

    # Find user
    user = User.query.filter_by(username=data['username']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is disabled'}), 403

    # Check site status
    site = Site.query.get(user.site_id)
    if site.subscription_status in ['suspended', 'cancelled']:
        return jsonify({'error': 'Subscription inactive'}), 403

    # Generate token
    token = generate_token(user)

    return jsonify({
        'token': token,
        'expires_in': 86400,
        'user': {
            'user_id': user.user_id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'access_level': user.access_level,
            'site_id': user.site_id
        }
    }), 200


@api_bp.route('/auth/refresh', methods=['POST'])
@token_required
def refresh_token(current_user):
    """
    Refresh JWT token

    POST /api/v1/auth/refresh
    Headers: Authorization: Bearer <token>

    Returns new token with extended expiration
    """
    token = generate_token(current_user)

    return jsonify({
        'token': token,
        'expires_in': 86400
    }), 200


@api_bp.route('/auth/verify', methods=['GET'])
@token_required
def verify(current_user):
    """
    Verify token is valid

    GET /api/v1/auth/verify
    Headers: Authorization: Bearer <token>
    """
    return jsonify({
        'valid': True,
        'user': {
            'user_id': current_user.user_id,
            'username': current_user.username,
            'access_level': current_user.access_level,
            'site_id': current_user.site_id
        }
    }), 200
