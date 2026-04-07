import unittest
import json
from app import create_app
from libs.db import db, session
from app.models.user import User

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            test_user = User(
                username='testuser',
                password='8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',
                phone='13800138000',
                email='test@example.com',
                real_name='Test User',
                role=User.ROLE_STUDENT
            )
            session.add(test_user)
            session.commit()
    
    def tearDown(self):
        with self.app.app_context():
            db.drop_all()
    
    def test_register(self):
        response = self.client.post('/api/auth/register', 
            data=json.dumps({
                'username': 'newuser',
                'phone': '13800138001',
                'password': '123456',
                'real_name': 'New User'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
    
    def test_login(self):
        response = self.client.post('/api/auth/login',
            data=json.dumps({
                'phone': '13800138000',
                'password': '123456'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('token', data)
    
    def test_login_with_wrong_password(self):
        response = self.client.post('/api/auth/login',
            data=json.dumps({
                'phone': '13800138000',
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main()