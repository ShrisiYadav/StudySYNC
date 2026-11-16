from flask import Blueprint, jsonify
from database import db, Notification, Steps, WaterIntake, SleepRecord, HeartRate, Goal
from middleware import token_required
from datetime import datetime, timedelta

notifications_bp = Blueprint('notifications', __name__)

def check_inactive_user(current_user):
    # Find most recent log time across all metrics
    latest_times = []
    
    steps_log = Steps.query.filter_by(user_id=current_user.id).order_by(Steps.logged_at.desc()).first()
    if steps_log:
        try:
            latest_times.append(datetime.strptime(steps_log.logged_at, '%Y-%m-%d %H:%M:%S'))
        except ValueError:
            pass
        
    water_log = WaterIntake.query.filter_by(user_id=current_user.id).order_by(WaterIntake.logged_at.desc()).first()
    if water_log:
        try:
            latest_times.append(datetime.strptime(water_log.logged_at, '%Y-%m-%d %H:%M:%S'))
        except ValueError:
            pass
        
    sleep_log = SleepRecord.query.filter_by(user_id=current_user.id).order_by(SleepRecord.logged_at.desc()).first()
    if sleep_log:
        try:
            latest_times.append(datetime.strptime(sleep_log.logged_at, '%Y-%m-%d %H:%M:%S'))
        except ValueError:
            pass
        
    hr_log = HeartRate.query.filter_by(user_id=current_user.id).order_by(HeartRate.logged_at.desc()).first()
    if hr_log:
        try:
            latest_times.append(datetime.strptime(hr_log.logged_at, '%Y-%m-%d %H:%M:%S'))
        except ValueError:
            pass

    latest_time = None
    if latest_times:
        latest_time = max(latest_times)
    else:
        # Fallback to user registration time
        try:
            latest_time = datetime.strptime(current_user.created_at, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            latest_time = datetime.now() - timedelta(hours=25) # force trigger if format is wrong

    # Check if latest activity is > 24 hours ago
    if datetime.now() - latest_time > timedelta(hours=24):
        # Look for existing unread inactivity notification
        title = "Platform Inactivity Alert"
        existing = Notification.query.filter_by(
            user_id=current_user.id,
            title=title,
            is_read=0
        ).first()
        
        if not existing:
            notif = Notification(
                user_id=current_user.id,
                title=title,
                message="Consistency is key to wellness! We noticed you haven't logged any health metrics in the last 24 hours. Let's record some stats!",
                type="warning"
            )
            db.session.add(notif)
            db.session.commit()

@notifications_bp.route('', methods=['GET'])
@token_required
def get_notifications(current_user):
    check_inactive_user(current_user)
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return jsonify({'notifications': [n.to_dict() for n in notifications]}), 200

@notifications_bp.route('/reminders', methods=['GET'])
@token_required
def get_reminders(current_user):
    # Run the inactivity check first
    check_inactive_user(current_user)
    
    reminders = []
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    # 1. Water Reminder (every 3 hours)
    latest_water = WaterIntake.query.filter_by(user_id=current_user.id).order_by(WaterIntake.logged_at.desc()).first()
    if latest_water:
        try:
            latest_time = datetime.strptime(latest_water.logged_at, '%Y-%m-%d %H:%M:%S')
            if datetime.now() - latest_time > timedelta(hours=3):
                reminders.append({
                    'type': 'water',
                    'title': 'Stay Hydrated',
                    'message': "It has been over 3 hours since your last logged water intake. Don't forget to drink water and log it!",
                    'severity': 'info'
                })
        except ValueError:
            pass
    else:
        reminders.append({
            'type': 'water',
            'title': 'Stay Hydrated',
            'message': "You haven't logged any water intake today. Keep tracking to meet your hydration targets!",
            'severity': 'info'
        })
        
    # 2. Daily Activity Reminder (Step Goal progress)
    steps_goal = Goal.query.filter_by(user_id=current_user.id, metric_type='steps').first()
    steps_log = Steps.query.filter_by(user_id=current_user.id, log_date=today_str).first()
    logged_steps = steps_log.count if steps_log else 0
    
    if steps_goal:
        target = int(steps_goal.target_value)
        if logged_steps < target:
            reminders.append({
                'type': 'activity',
                'title': 'Daily Movement Target',
                'message': f"You have logged {logged_steps:,} steps out of your {target:,} steps target today. Keep moving!",
                'severity': 'warning'
            })
    else:
        reminders.append({
            'type': 'activity',
            'title': 'Set a Step Goal',
            'message': 'You have not configured a daily step goal yet. Configure a goal to track your target activity levels!',
            'severity': 'info'
        })
        
    # 3. Sleep Reminder
    sleep_log = SleepRecord.query.filter_by(user_id=current_user.id, log_date=today_str).first()
    if not sleep_log:
        reminders.append({
            'type': 'sleep',
            'title': 'Nightly Rest',
            'message': "Don't forget to record your sleep hours for last night to track rest patterns on your graphs.",
            'severity': 'info'
        })
    else:
        duration = sleep_log.duration_hours
        if duration < 7.0:
            reminders.append({
                'type': 'sleep',
                'title': 'Sufficient Sleep Alert',
                'message': f"You logged {duration} hours of sleep today. Recommended guidelines suggest 7–9 hours for optimal recovery.",
                'severity': 'warning'
            })
            
    return jsonify({'reminders': reminders}), 200

@notifications_bp.route('/read', methods=['POST'])
@token_required
def read_all_notifications(current_user):
    Notification.query.filter_by(user_id=current_user.id, is_read=0).update({Notification.is_read: 1})
    db.session.commit()
    return jsonify({'message': 'All notifications marked as read'}), 200

@notifications_bp.route('/read/<int:notif_id>', methods=['POST'])
@token_required
def read_notification(current_user, notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first()
    if not notif:
        return jsonify({'message': 'Notification not found'}), 404
    notif.is_read = 1
    db.session.commit()
    return jsonify({'message': 'Notification marked as read'}), 200

@notifications_bp.route('/<int:notif_id>', methods=['DELETE'])
@token_required
def delete_notification(current_user, notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first()
    if not notif:
        return jsonify({'message': 'Notification not found'}), 404
    db.session.delete(notif)
    db.session.commit()
    return jsonify({'message': 'Notification deleted successfully'}), 200
