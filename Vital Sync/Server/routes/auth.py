import jwt
import datetime
from flask import Blueprint, request, jsonify, make_response, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, User
from middleware import token_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    age = data.get('age')
    gender = data.get('gender')
    role = data.get('role', 'user')

    if not all([name, email, password, age, gender]):
        return jsonify({'message': 'All registration fields are required'}), 400

    email = str(email).strip().lower()
    name = str(name).strip()
    gender = str(gender).strip().lower()
    
    try:
        age = int(age)
        if age <= 0:
            raise ValueError()
    except ValueError:
        return jsonify({'message': 'Age must be a valid positive integer'}), 400

    if gender not in ['male', 'female', 'other']:
        return jsonify({'message': 'Gender must be male, female, or other'}), 400

    if role not in ['user', 'admin']:
        role = 'user'

    # Check database for existing user
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email address is already registered'}), 409

    hashed_password = generate_password_hash(password)
    new_user = User(
        name=name,
        email=email,
        password_hash=hashed_password,
        age=age,
        gender=gender,
        role=role
    )
    
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Registration successful', 'user_id': new_user.id}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400

    email = str(email).strip().lower()
    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Invalid email credentials or password'}), 401

    if getattr(user, 'is_active', 1) == 0:
        return jsonify({'message': 'This account has been disabled. Please contact support.'}), 403

    # Generate JWT Token for stateless authentication
    token_exp = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    token = jwt.encode(
        {'user_id': user.id, 'role': user.role, 'exp': token_exp},
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

    response = make_response(jsonify({
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        }
    }))
    
    # Store token in HTTPOnly Cookie to prevent XSS theft
    response.set_cookie(
        'token',
        token,
        httponly=True,
        samesite='Lax',
        max_age=24 * 60 * 60,
        secure=False
    )
    
    return response

@auth_bp.route('/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({'message': 'Logged out successfully'}))
    response.delete_cookie('token')
    return response

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify(current_user.to_dict()), 200
