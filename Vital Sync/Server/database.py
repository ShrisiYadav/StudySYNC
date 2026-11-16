from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    is_active = db.Column(db.Integer, nullable=False, default=1) # 0 for disabled, 1 for active
    created_at = db.Column(db.String(30), nullable=False, default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def __init__(
        self,
        name: str,
        email: str,
        password_hash: str,
        age: int,
        gender: str,
        role: str = 'user',
        is_active: int = 1,
        **kwargs
    ) -> None:
        super().__init__(
            name=name,
            email=email,
            password_hash=password_hash,
            age=age,
            gender=gender,
            role=role,
            is_active=is_active,
            **kwargs
        )

    # Relationships
    steps_logs = db.relationship('Steps', backref='user', cascade='all, delete-orphan', lazy=True)
    water_logs = db.relationship('WaterIntake', backref='user', cascade='all, delete-orphan', lazy=True)
    sleep_logs = db.relationship('SleepRecord', backref='user', cascade='all, delete-orphan', lazy=True)
    heart_rate_logs = db.relationship('HeartRate', backref='user', cascade='all, delete-orphan', lazy=True)
    goals = db.relationship('Goal', backref='user', cascade='all, delete-orphan', lazy=True)
    notifications = db.relationship('Notification', backref='user', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'age': self.age,
            'gender': self.gender,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at
        }

class Steps(db.Model):
    __tablename__ = 'steps'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    count = db.Column(db.Integer, nullable=False)
    log_date = db.Column(db.String(10), nullable=False) # YYYY-MM-DD
    logged_at = db.Column(db.String(30), nullable=False, default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'log_date', name='uq_steps_user_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'count': self.count,
            'log_date': self.log_date,
            'logged_at': self.logged_at
        }

class WaterIntake(db.Model):
    __tablename__ = 'water_intake'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    amount_ml = db.Column(db.Float, nullable=False)
    log_date = db.Column(db.String(10), nullable=False) # YYYY-MM-DD
    logged_at = db.Column(db.String(30), nullable=False, default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount_ml': self.amount_ml,
            'log_date': self.log_date,
            'logged_at': self.logged_at
        }

class SleepRecord(db.Model):
    __tablename__ = 'sleep_records'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    duration_hours = db.Column(db.Float, nullable=False)
    log_date = db.Column(db.String(10), nullable=False) # YYYY-MM-DD
    logged_at = db.Column(db.String(30), nullable=False, default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'log_date', name='uq_sleep_user_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'duration_hours': self.duration_hours,
            'log_date': self.log_date,
            'logged_at': self.logged_at
        }

class HeartRate(db.Model):
    __tablename__ = 'heart_rate'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    bpm = db.Column(db.Integer, nullable=False)
    log_date = db.Column(db.String(10), nullable=False) # YYYY-MM-DD
    logged_at = db.Column(db.String(30), nullable=False, default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'bpm': self.bpm,
            'log_date': self.log_date,
            'logged_at': self.logged_at
        }

class Goal(db.Model):
    __tablename__ = 'goals'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    metric_type = db.Column(db.String(20), nullable=False) # 'steps', 'water', 'sleep'
    target_value = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.String(30), nullable=False, default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    updated_at = db.Column(db.String(30), nullable=False, default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'metric_type', name='uq_goals_user_metric'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'metric_type': self.metric_type,
            'target_value': self.target_value,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(30), nullable=False, default='info') # 'info', 'goal_reached', 'warning'
    is_read = db.Column(db.Integer, nullable=False, default=0) # 0 for False, 1 for True
    created_at = db.Column(db.String(30), nullable=False, default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': bool(self.is_read),
            'created_at': self.created_at
        }
