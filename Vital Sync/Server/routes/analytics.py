from flask import Blueprint, request, jsonify
from database import db, Steps, WaterIntake, SleepRecord, HeartRate
from middleware import token_required
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/trends', methods=['GET'])
@token_required
def get_trends(current_user):
    try:
        days = int(request.args.get('days', 7))
        if days <= 0 or days > 30:
            days = 7
    except ValueError:
        days = 7

    today = datetime.now().date()
    dates_list = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]
    dates_list.reverse()

    start_date = dates_list[0]
    end_date = dates_list[-1]

    # Pre-fetch and aggregate Steps (UPSERT maps single daily entries)
    steps_records = Steps.query.filter(
        Steps.user_id == current_user.id,
        Steps.log_date >= start_date,
        Steps.log_date <= end_date
    ).all()
    steps_map = {r.log_date: r.count for r in steps_records}

    # Pre-fetch and aggregate Water (multiple entries summed)
    water_records = WaterIntake.query.filter(
        WaterIntake.user_id == current_user.id,
        WaterIntake.log_date >= start_date,
        WaterIntake.log_date <= end_date
    ).all()
    water_map = {}
    for r in water_records:
        water_map[r.log_date] = water_map.get(r.log_date, 0.0) + r.amount_ml

    # Pre-fetch and aggregate Sleep
    sleep_records = SleepRecord.query.filter(
        SleepRecord.user_id == current_user.id,
        SleepRecord.log_date >= start_date,
        SleepRecord.log_date <= end_date
    ).all()
    sleep_map = {r.log_date: r.duration_hours for r in sleep_records}

    # Pre-fetch and aggregate Heart Rate (averaged per date)
    hr_records = HeartRate.query.filter(
        HeartRate.user_id == current_user.id,
        HeartRate.log_date >= start_date,
        HeartRate.log_date <= end_date
    ).all()
    hr_map = {}
    hr_counts = {}
    for r in hr_records:
        hr_map[r.log_date] = hr_map.get(r.log_date, 0.0) + r.bpm
        hr_counts[r.log_date] = hr_counts.get(r.log_date, 0) + 1
    
    hr_avg_map = {}
    for d, total_bpm in hr_map.items():
        hr_avg_map[d] = round(total_bpm / hr_counts[d], 1)

    response_data = {
        'dates': dates_list,
        'steps': [steps_map.get(d, 0) for d in dates_list],
        'water': [water_map.get(d, 0.0) for d in dates_list],
        'sleep': [sleep_map.get(d, 0.0) for d in dates_list],
        'heart_rate': [hr_avg_map.get(d, 0) for d in dates_list]
    }

    return jsonify(response_data), 200
