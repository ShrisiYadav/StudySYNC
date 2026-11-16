from flask import Blueprint, request, jsonify
from database import db, Steps, WaterIntake, SleepRecord, HeartRate, Notification, Goal
from middleware import token_required
from datetime import datetime

health_bp = Blueprint('health', __name__)

@health_bp.route('/log', methods=['POST'])
@token_required
def log_metric(current_user):
    data = request.get_json() or {}
    metric_type = data.get('metric_type')
    value = data.get('value')
    log_date = data.get('date')

    if not metric_type or value is None:
        return jsonify({'message': 'metric_type and value are required'}), 400

    if metric_type not in ['steps', 'water', 'sleep', 'heart_rate']:
        return jsonify({'message': f'Invalid metric type: {metric_type}'}), 400

    try:
        value = float(value)
        if value < 0:
            return jsonify({'message': 'Value cannot be negative'}), 400
    except ValueError:
        return jsonify({'message': 'Value must be a number'}), 400

    if not log_date:
        log_date = datetime.now().strftime('%Y-%m-%d')
    else:
        try:
            datetime.strptime(log_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'message': 'Date must be in YYYY-MM-DD format'}), 400

    # Log based on type
    if metric_type == 'steps':
        if not value.is_integer():
            return jsonify({'message': 'Steps value must be a valid integer'}), 400
        steps_val = int(value)

        # Incremental UPSERT daily steps
        record = Steps.query.filter_by(user_id=current_user.id, log_date=log_date).first()
        if record:
            record.count += steps_val
            record.logged_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            record = Steps(user_id=current_user.id, count=steps_val, log_date=log_date)
            db.session.add(record)
        
        db.session.commit()
        check_and_trigger_goal_notification(current_user.id, 'steps', log_date)
        return jsonify({'message': 'Steps logged successfully', 'log': record.to_dict()}), 200

    elif metric_type == 'water':
        # Add a incremental water intake record
        record = WaterIntake(user_id=current_user.id, amount_ml=value, log_date=log_date)
        db.session.add(record)
        db.session.commit()
        check_and_trigger_goal_notification(current_user.id, 'water', log_date)
        return jsonify({'message': 'Water intake logged successfully', 'log': record.to_dict()}), 200

    elif metric_type == 'sleep':
        if value > 24.0:
            return jsonify({'message': 'Sleep duration cannot exceed 24 hours'}), 400

        # Update sleep records for the day if already exists
        record = SleepRecord.query.filter_by(user_id=current_user.id, log_date=log_date).first()
        if record:
            record.duration_hours = value
            record.logged_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            record = SleepRecord(user_id=current_user.id, duration_hours=value, log_date=log_date)
            db.session.add(record)
        
        db.session.commit()
        check_and_trigger_goal_notification(current_user.id, 'sleep', log_date)
        return jsonify({'message': 'Sleep record logged successfully', 'log': record.to_dict()}), 200

    elif metric_type == 'heart_rate':
        if not value.is_integer():
            return jsonify({'message': 'Heart rate bpm must be a valid integer'}), 400
        bpm_val = int(value)
        if bpm_val < 30 or bpm_val > 250:
            return jsonify({'message': 'Heart rate must be between 30 and 250 bpm'}), 400

        record = HeartRate(user_id=current_user.id, bpm=bpm_val, log_date=log_date)
        db.session.add(record)
        db.session.commit()

        # Trigger alert notifications for high/low heart rate logs
        if bpm_val > 150:
            trigger_warning_notification(current_user.id, 'High Heart Rate Alert', f'Your heart rate measurement of {bpm_val} bpm is elevated. Take a rest.')
        elif bpm_val < 50:
            trigger_warning_notification(current_user.id, 'Low Heart Rate Alert', f'Your heart rate measurement of {bpm_val} bpm is low. Consult a healthcare provider if you feel dizzy.')

        return jsonify({'message': 'Heart rate logged successfully', 'log': record.to_dict()}), 200

def check_and_trigger_goal_notification(user_id, metric, log_date):
    goal = Goal.query.filter_by(user_id=user_id, metric_type=metric).first()
    if not goal:
        return

    total_val = 0
    if metric == 'steps':
        rec = Steps.query.filter_by(user_id=user_id, log_date=log_date).first()
        total_val = rec.count if rec else 0
    elif metric == 'water':
        logs = WaterIntake.query.filter_by(user_id=user_id, log_date=log_date).all()
        total_val = sum(l.amount_ml for l in logs)
    elif metric == 'sleep':
        rec = SleepRecord.query.filter_by(user_id=user_id, log_date=log_date).first()
        total_val = rec.duration_hours if rec else 0

    if total_val >= goal.target_value:
        title = f'Goal Reached: {metric.capitalize()}'
        existing = Notification.query.filter(
            Notification.user_id == user_id,
            Notification.title == title,
            Notification.created_at.like(f'{log_date}%')
        ).first()
        
        if not existing:
            notif = Notification(
                user_id=user_id,
                title=title,
                message=f'Congratulations! You met your daily {metric} goal of {int(goal.target_value)} (Logged: {int(total_val)}).',
                type='goal_reached'
            )
            db.session.add(notif)
            db.session.commit()

def trigger_warning_notification(user_id, title, message):
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type='warning'
    )
    db.session.add(notif)
    db.session.commit()

@health_bp.route('/history', methods=['GET'])
@token_required
def get_history(current_user):
    metric_type = request.args.get('metric_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not metric_type:
        return jsonify({'message': 'metric_type parameter is required'}), 400

    if metric_type == 'steps':
        query = Steps.query.filter_by(user_id=current_user.id)
    elif metric_type == 'water':
        query = WaterIntake.query.filter_by(user_id=current_user.id)
    elif metric_type == 'sleep':
        query = SleepRecord.query.filter_by(user_id=current_user.id)
    elif metric_type == 'heart_rate':
        query = HeartRate.query.filter_by(user_id=current_user.id)
    else:
        return jsonify({'message': 'Invalid metric_type'}), 400

    if start_date:
        if metric_type == 'steps':
            query = query.filter(Steps.log_date >= start_date)
        elif metric_type == 'water':
            query = query.filter(WaterIntake.log_date >= start_date)
        elif metric_type == 'sleep':
            query = query.filter(SleepRecord.log_date >= start_date)
        elif metric_type == 'heart_rate':
            query = query.filter(HeartRate.log_date >= start_date)
            
    if end_date:
        if metric_type == 'steps':
            query = query.filter(Steps.log_date <= end_date)
        elif metric_type == 'water':
            query = query.filter(WaterIntake.log_date <= end_date)
        elif metric_type == 'sleep':
            query = query.filter(SleepRecord.log_date <= end_date)
        elif metric_type == 'heart_rate':
            query = query.filter(HeartRate.log_date <= end_date)

    if metric_type == 'steps':
        records = query.order_by(Steps.log_date.asc(), Steps.logged_at.asc()).all()
    elif metric_type == 'water':
        records = query.order_by(WaterIntake.log_date.asc(), WaterIntake.logged_at.asc()).all()
    elif metric_type == 'sleep':
        records = query.order_by(SleepRecord.log_date.asc(), SleepRecord.logged_at.asc()).all()
    else:
        records = query.order_by(HeartRate.log_date.asc(), HeartRate.logged_at.asc()).all()

    return jsonify({'logs': [r.to_dict() for r in records]}), 200

@health_bp.route('/log/<int:log_id>', methods=['DELETE'])
@token_required
def delete_log(current_user, log_id):
    metric_type = request.args.get('metric_type')
    if not metric_type:
        return jsonify({'message': 'metric_type parameter is required for deletion'}), 400

    if metric_type == 'steps':
        record = Steps.query.filter_by(id=log_id, user_id=current_user.id).first()
    elif metric_type == 'water':
        record = WaterIntake.query.filter_by(id=log_id, user_id=current_user.id).first()
    elif metric_type == 'sleep':
        record = SleepRecord.query.filter_by(id=log_id, user_id=current_user.id).first()
    elif metric_type == 'heart_rate':
        record = HeartRate.query.filter_by(id=log_id, user_id=current_user.id).first()
    else:
        return jsonify({'message': 'Invalid metric_type'}), 400

    if not record:
        return jsonify({'message': 'Record not found'}), 404

    db.session.delete(record)
    db.session.commit()
    return jsonify({'message': 'Health record deleted successfully'}), 200
