import jwt
from functools import wraps
from flask import request, jsonify, current_app
from database import db, User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Check cookies first for web application
        if 'token' in request.cookies:
            token = request.cookies.get('token')
        # Fallback to Authorization header for API flexibility
        elif 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Authentication token is missing'}), 401
        
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = db.session.get(User, payload['user_id'])
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
            if getattr(current_user, 'is_active', 1) == 0:
                return jsonify({'message': 'Your account has been disabled. Please contact support.'}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Authentication token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid authentication token'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'message': 'Administrator access privileges required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated
