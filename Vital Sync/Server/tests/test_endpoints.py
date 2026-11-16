import os
import tempfile
import unittest
import json
import sys

# Ensure server folder is on path to import database and app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database import db, User, Steps, Goal

class VitalSyncTestCase(unittest.TestCase):
    def setUp(self):
        # Create temp file first
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Pass configuration overrides to create isolated context
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{self.db_path}',
            'SECRET_KEY': 'testing_key'
        })
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Seed standard user
            from werkzeug.security import generate_password_hash
            user = User(
                name='Test User',
                email='test@example.com',
                password_hash=generate_password_hash('Password123'),
                age=22,
                gender='male',
                role='user'
            )
            db.session.add(user)
            db.session.commit()
            
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass
        
    def test_ping(self):
        rv = self.client.get('/api/ping')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'VitalSync API Server is Active', rv.data)
        
    def test_register_login(self):
        # Register a new user
        rv = self.client.post('/api/auth/register', json={
            'name': 'Priya',
            'email': 'priya@example.com',
            'password': 'Password123',
            'age': 25,
            'gender': 'female'
        })
        self.assertEqual(rv.status_code, 201)
        
        # Login user
        rv = self.client.post('/api/auth/login', json={
            'email': 'priya@example.com',
            'password': 'Password123'
        })
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertIn('token', data)
        self.assertEqual(data['user']['name'], 'Priya')
        
    def test_health_logging(self):
        # Login user to set session cookies
        self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'Password123'
        })
        
        # Log Steps (Valid integer)
        rv = self.client.post('/api/health/log', json={
            'metric_type': 'steps',
            'value': 5000,
            'date': '2026-06-04'
        })
        self.assertEqual(rv.status_code, 200)

        # Log Steps (Invalid decimal/float)
        rv = self.client.post('/api/health/log', json={
            'metric_type': 'steps',
            'value': 5000.5,
            'date': '2026-06-04'
        })
        self.assertEqual(rv.status_code, 400)
        data = json.loads(rv.data)
        self.assertEqual(data['message'], 'Steps value must be a valid integer')

        # Log Heart Rate (Invalid decimal/float)
        rv = self.client.post('/api/health/log', json={
            'metric_type': 'heart_rate',
            'value': 72.8,
            'date': '2026-06-04'
        })
        self.assertEqual(rv.status_code, 400)
        data = json.loads(rv.data)
        self.assertEqual(data['message'], 'Heart rate bpm must be a valid integer')
        
        # Retrieve logged steps
        rv = self.client.get('/api/health/history?metric_type=steps')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEqual(len(data['logs']), 1)
        self.assertEqual(data['logs'][0]['count'], 5000)
        
    def test_goal_setting(self):
        # Login user
        self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'Password123'
        })
        
        # Set Steps Goal
        rv = self.client.post('/api/goals', json={
            'metric_type': 'steps',
            'target_value': 8000
        })
        self.assertEqual(rv.status_code, 200)
        
        # Retrieve progress
        rv = self.client.get('/api/goals')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEqual(data['goals']['steps'], 8000)

    def test_admin_enhancements(self):
        # Login admin user (created by default seed on app create)
        rv = self.client.post('/api/auth/login', json={
            'email': 'admin@vitalsync.com',
            'password': 'AdminPassword123'
        })
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        admin_token = data['token']
        self.client.set_cookie('token', admin_token)

        # Create a user to manage
        self.client.post('/api/auth/register', json={
            'name': 'Rahul',
            'email': 'rahul@example.com',
            'password': 'Password123',
            'age': 20,
            'gender': 'male'
        })
        
        # Get user ID
        with self.app.app_context():
            user = User.query.filter_by(email='rahul@example.com').first()
            user_id = user.id

        # 1. Test profile edit
        rv = self.client.put(f'/api/admin/users/{user_id}', json={
            'name': 'Rahul Sharma',
            'email': 'rahul.sharma@example.com',
            'age': 21,
            'gender': 'male',
            'role': 'user'
        })
        self.assertEqual(rv.status_code, 200)
        
        # Verify changes in DB
        with self.app.app_context():
            updated_user = db.session.get(User, user_id)
            self.assertEqual(updated_user.name, 'Rahul Sharma')
            self.assertEqual(updated_user.email, 'rahul.sharma@example.com')
            self.assertEqual(updated_user.age, 21)

        # 2. Test status toggle (disable account)
        rv = self.client.post(f'/api/admin/users/{user_id}/toggle-status')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEqual(data['is_active'], 0)

        # Try to login with disabled account (should fail with 403 Forbidden)
        rv = self.client.post('/api/auth/login', json={
            'email': 'rahul.sharma@example.com',
            'password': 'Password123'
        })
        self.assertEqual(rv.status_code, 403)
        self.assertIn(b'This account has been disabled', rv.data)

        # Toggle status back (enable account)
        rv = self.client.post(f'/api/admin/users/{user_id}/toggle-status')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEqual(data['is_active'], 1)

        # Login should now succeed
        rv = self.client.post('/api/auth/login', json={
            'email': 'rahul.sharma@example.com',
            'password': 'Password123'
        })
        self.assertEqual(rv.status_code, 200)

        # Restore admin token in the session cookie to perform admin actions
        self.client.set_cookie('token', admin_token)

        # 3. Test password reset
        rv = self.client.post(f'/api/admin/users/{user_id}/reset-password', json={
            'password': 'NewPassword123'
        })
        self.assertEqual(rv.status_code, 200)

        # Login with old password should fail
        rv = self.client.post('/api/auth/login', json={
            'email': 'rahul.sharma@example.com',
            'password': 'Password123'
        })
        self.assertEqual(rv.status_code, 401)

        # Login with new password should succeed
        rv = self.client.post('/api/auth/login', json={
            'email': 'rahul.sharma@example.com',
            'password': 'NewPassword123'
        })
        self.assertEqual(rv.status_code, 200)

if __name__ == '__main__':
    unittest.main()
