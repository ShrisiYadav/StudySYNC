import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, send_from_directory
from database import db, User
from werkzeug.security import generate_password_hash

# Import Blueprints
from routes.auth import auth_bp
from routes.health import health_bp
from routes.goals import goals_bp
from routes.analytics import analytics_bp
from routes.admin import admin_bp
from routes.notifications import notifications_bp

def load_env():
    # Look for .env in workspace root and Server root
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, val = line.split('=', 1)
                        os.environ[key.strip()] = val.strip()
            break

def create_app(config_overrides=None):
    app = Flask(__name__)
    
    load_env()
    
    # Configure database URI inside Server directory
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'vitalsync_secret_key_2026_secure')

    if config_overrides:
        app.config.update(config_overrides)

    # Initialize SQLAlchemy database instance
    db.init_app(app)

    # Dynamic CORS reflections for local credentials support
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        return response

    @app.route('/api/ping', methods=['GET'])
    def ping():
        return jsonify({'message': 'VitalSync API Server is Active'}), 200

    # Register Blueprint routes
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(health_bp, url_prefix='/api/health')
    app.register_blueprint(goals_bp, url_prefix='/api/goals')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')

    # Serve Client static files
    client_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Client')

    @app.route('/')
    def serve_index():
        if os.path.exists(os.path.join(client_dir, 'index.html')):
            return send_from_directory(client_dir, 'index.html')
        return jsonify({'message': 'VitalSync API Server is Active'}), 200

    @app.route('/<path:filename>')
    def serve_static(filename):
        if filename.startswith('api/'):
            return jsonify({'message': 'Endpoint not found'}), 404
        file_path = os.path.join(client_dir, filename)
        if os.path.isfile(file_path):
            return send_from_directory(client_dir, filename)
        if os.path.isdir(file_path) and os.path.isfile(os.path.join(file_path, 'index.html')):
            return send_from_directory(file_path, 'index.html')
        return jsonify({'message': 'File not found'}), 404

    # Seed Database tables and admin account
    with app.app_context():
        db.create_all()
        # Migration: Check if is_active column exists, if not ALTER TABLE
        try:
            db.session.execute(db.text("SELECT is_active FROM users LIMIT 1"))
        except Exception:
            db.session.rollback()
            try:
                db.session.execute(db.text("ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1"))
                db.session.commit()
                print("Database migration: Added is_active column to users table.")
            except Exception as ex:
                print("Failed to run database migration:", ex)
        
        # Check if default admin exists
        admin_email = 'admin@vitalsync.com'
        admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            admin_user = User(
                name='System Administrator',
                email=admin_email,
                password_hash=generate_password_hash('AdminPassword123'),
                age=30,
                gender='other',
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Seeded default administrator: admin@vitalsync.com / AdminPassword123")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=True)
