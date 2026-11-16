from flask import Blueprint, request, jsonify
from database import db, Goal, Steps, WaterIntake, SleepRecord
from middleware import token_required
from datetime import datetime

goals_bp = Blueprint('goals', __name__)

@goals_bp.route('', methods=['POST'])
@token_required
def set_goal(current_user):
    data = request.get_json() or {}
    metric_type = data.get('metric_type')
    target_value = data.get('target_value')

    if not metric_type or target_value is None:
        return jsonify({'message': 'metric_type and target_value are required'}), 400

    if metric_type not in ['steps', 'water', 'sleep']:
        return jsonify({'message': f'Goal tracking not supported for: {metric_type}'}), 400

    try:
        target_value = float(target_value)
        if target_value <= 0:
            return jsonify({'message': 'Goal target value must be positive'}), 400
    except ValueError:
        return jsonify({'message': 'Goal target value must be a number'}), 400

    # Insert or update goal
    goal = Goal.query.filter_by(user_id=current_user.id, metric_type=metric_type).first()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if goal:
        goal.target_value = target_value
        goal.updated_at = now_str
    else:
        goal = Goal(
            user_id=current_user.id,
            metric_type=metric_type,
            target_value=target_value,
            created_at=now_str,
            updated_at=now_str
        )
        db.session.add(goal)
    
    db.session.commit()
    return jsonify({'message': 'Goal configured successfully', 'goal': goal.to_dict()}), 200

@goals_bp.route('', methods=['GET'])
@token_required
def get_goals(current_user):
    goals_list = Goal.query.filter_by(user_id=current_user.id).all()
    today_str = datetime.now().strftime('%Y-%m-%d')

    # Default targets
    goals_dict = {
        'steps': 0,
        'water': 0,
        'sleep': 0
    }
    for g in goals_list:
        goals_dict[g.metric_type] = g.target_value

    # Today's logs aggregations
    steps_log = Steps.query.filter_by(user_id=current_user.id, log_date=today_str).first()
    logged_steps = steps_log.count if steps_log else 0

    water_logs = WaterIntake.query.filter_by(user_id=current_user.id, log_date=today_str).all()
    logged_water = sum(w.amount_ml for w in water_logs)

    sleep_log = SleepRecord.query.filter_by(user_id=current_user.id, log_date=today_str).first()
    logged_sleep = sleep_log.duration_hours if sleep_log else 0

    def calc_progress(logged, target):
        if target <= 0:
            return {'logged': logged, 'percentage': 0.0}
        percent = round((logged / target) * 100, 2)
        return {'logged': logged, 'percentage': min(percent, 100.0)}

    progress = {
        'steps': calc_progress(logged_steps, goals_dict['steps']),
        'water': calc_progress(logged_water, goals_dict['water']),
        'sleep': calc_progress(logged_sleep, goals_dict['sleep'])
    }

    return jsonify({
        'goals': goals_dict,
        'progress': progress
    }), 200
