from flask import Blueprint, request, jsonify
from database import db, User, Steps, WaterIntake, SleepRecord, HeartRate
from middleware import token_required, admin_required
from sqlalchemy import func
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_users(current_user):
    search_query = request.args.get('search', '').strip()
    if search_query:
        users = User.query.filter(
            (User.name.like(f'%{search_query}%')) | 
            (User.email.like(f'%{search_query}%'))
        ).all()
    else:
        users = User.query.all()
    
    return jsonify({'users': [u.to_dict() for u in users]}), 200

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(current_user, user_id):
    if user_id == current_user.id:
        return jsonify({'message': 'Cannot delete your own administrative account'}), 400

    user_to_delete = db.session.get(User, user_id)
    if not user_to_delete:
        return jsonify({'message': 'User not found'}), 404

    # Cascade deletes to foreign tables
    db.session.delete(user_to_delete)
    db.session.commit()

    return jsonify({'message': 'User and all associated data deleted successfully'}), 200

@admin_bp.route('/records', methods=['GET'])
@token_required
@admin_required
def get_all_records(current_user):
    steps = Steps.query.order_by(Steps.logged_at.desc()).limit(50).all()
    water = WaterIntake.query.order_by(WaterIntake.logged_at.desc()).limit(50).all()
    sleep = SleepRecord.query.order_by(SleepRecord.logged_at.desc()).limit(50).all()
    hr = HeartRate.query.order_by(HeartRate.logged_at.desc()).limit(50).all()

    all_logs = []
    
    for s in steps:
        all_logs.append({
            'id': s.id,
            'user_name': s.user.name,
            'user_email': s.user.email,
            'metric_type': 'steps',
            'value': s.count,
            'log_date': s.log_date,
            'logged_at': s.logged_at
        })
    for w in water:
        all_logs.append({
            'id': w.id,
            'user_name': w.user.name,
            'user_email': w.user.email,
            'metric_type': 'water',
            'value': w.amount_ml,
            'log_date': w.log_date,
            'logged_at': w.logged_at
        })
    for sl in sleep:
        all_logs.append({
            'id': sl.id,
            'user_name': sl.user.name,
            'user_email': sl.user.email,
            'metric_type': 'sleep',
            'value': sl.duration_hours,
            'log_date': sl.log_date,
            'logged_at': sl.logged_at
        })
    for h in hr:
        all_logs.append({
            'id': h.id,
            'user_name': h.user.name,
            'user_email': h.user.email,
            'metric_type': 'heart_rate',
            'value': h.bpm,
            'log_date': h.log_date,
            'logged_at': h.logged_at
        })

    all_logs.sort(key=lambda x: x['logged_at'], reverse=True)
    return jsonify({'records': all_logs[:100]}), 200

@admin_bp.route('/records/<int:log_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_record(current_user, log_id):
    metric_type = request.args.get('metric_type')
    if not metric_type:
        return jsonify({'message': 'metric_type parameter is required for deletion'}), 400

    if metric_type == 'steps':
        record = db.session.get(Steps, log_id)
    elif metric_type == 'water':
        record = db.session.get(WaterIntake, log_id)
    elif metric_type == 'sleep':
        record = db.session.get(SleepRecord, log_id)
    elif metric_type == 'heart_rate':
        record = db.session.get(HeartRate, log_id)
    else:
        return jsonify({'message': 'Invalid metric_type'}), 400

    if not record:
        return jsonify({'message': 'Record not found'}), 404

    db.session.delete(record)
    db.session.commit()
    return jsonify({'message': 'Record successfully deleted by administrator'}), 200

@admin_bp.route('/metrics', methods=['GET'])
@token_required
@admin_required
def get_platform_metrics(current_user):
    total_users = User.query.count()
    steps_count = Steps.query.count()
    water_count = WaterIntake.query.count()
    sleep_count = SleepRecord.query.count()
    hr_count = HeartRate.query.count()
    total_logs = steps_count + water_count + sleep_count + hr_count

    # User registration growth grouped by month (YYYY-MM substring matching)
    growth_query = db.session.query(
        func.substr(User.created_at, 1, 7).label('month'),
        func.count(User.id).label('count')
    ).group_by('month').order_by('month').all()

    growth = {
        'months': [r[0] for r in growth_query],
        'counts': [r[1] for r in growth_query]
    }

    return jsonify({
        'total_users': total_users,
        'total_logs': total_logs,
        'activity': {
            'steps': steps_count,
            'water': water_count,
            'sleep': sleep_count,
            'heart_rate': hr_count
        },
        'growth': growth
    }), 200

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@token_required
@admin_required
def reset_password(current_user, user_id):
    data = request.get_json() or {}
    new_password = data.get('password')
    if not new_password or len(str(new_password)) < 8:
        return jsonify({'message': 'Password must be at least 8 characters long'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    user.password_hash = generate_password_hash(str(new_password))
    db.session.commit()
    return jsonify({'message': 'Password successfully reset'}), 200

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@token_required
@admin_required
def toggle_user_status(current_user, user_id):
    if user_id == current_user.id:
        return jsonify({'message': 'Cannot disable your own administrative account'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    user.is_active = 0 if getattr(user, 'is_active', 1) == 1 else 1
    db.session.commit()
    status_str = 'disabled' if user.is_active == 0 else 'enabled'
    return jsonify({'message': f'User account successfully {status_str}', 'is_active': user.is_active}), 200

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
def update_user_profile(current_user, user_id):
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    age = data.get('age')
    gender = data.get('gender')
    role = data.get('role')

    if not all([name, email, age, gender, role]):
        return jsonify({'message': 'Name, email, age, gender, and role are required'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    email = str(email).strip().lower()
    name = str(name).strip()
    gender = str(gender).strip().lower()
    role = str(role).strip().lower()

    try:
        age = int(age)
        if age <= 0:
            raise ValueError()
    except ValueError:
        return jsonify({'message': 'Age must be a valid positive integer'}), 400

    if gender not in ['male', 'female', 'other']:
        return jsonify({'message': 'Gender must be male, female, or other'}), 400

    if role not in ['user', 'admin']:
        return jsonify({'message': 'Role must be user or admin'}), 400

    # Ensure email is not already taken by another user
    existing_user = User.query.filter(User.email == email, User.id != user_id).first()
    if existing_user:
        return jsonify({'message': 'Email address is already registered to another account'}), 409

    # If the admin attempts to change their own role to 'user'
    if user_id == current_user.id and role != 'admin':
        return jsonify({'message': 'Cannot demote your own administrative role'}), 400

    user.name = name
    user.email = email
    user.age = age
    user.gender = gender
    user.role = role
    db.session.commit()

    return jsonify({'message': 'User profile successfully updated', 'user': user.to_dict()}), 200
