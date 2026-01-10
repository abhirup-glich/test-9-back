import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from flask.testing import FlaskClient
import sys
import os
from datetime import datetime

# Add the current directory to sys.path so we can import app and config
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from main import create_app
    from services import AdminService
except ImportError:
    # Fallback for when running from a different directory context
    from .main import create_app
    from .services import AdminService

class TestAdminRoutes(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['JWT_SECRET_KEY'] = 'test-secret'
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    @patch('services.AdminService.get_all_students')
    @patch('flask_jwt_extended.view_decorators.verify_jwt_in_request')
    @patch('routes.get_jwt')
    def test_get_students_success(self, mock_get_jwt, mock_verify_jwt, mock_get_all_students):
        # Mock JWT auth
        mock_get_jwt.return_value = {"role": "admin"}
        mock_verify_jwt.return_value = None
        
        # Mock Service response
        mock_get_all_students.return_value = [
            {"name": "Test Student", "roll_number": "123", "email": "test@example.com"}
        ]

        response = self.client.get('/api/students')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('students', response.json)
        self.assertEqual(len(response.json['students']), 1)
        self.assertEqual(response.json['students'][0]['name'], "Test Student")

    @patch('flask_jwt_extended.view_decorators.verify_jwt_in_request')
    @patch('routes.get_jwt')
    def test_get_students_unauthorized(self, mock_get_jwt, mock_verify_jwt):
        # Mock JWT auth as non-admin
        mock_get_jwt.return_value = {"role": "student"}
        mock_verify_jwt.return_value = None

        response = self.client.get('/api/students')
        
        self.assertEqual(response.status_code, 403)

    @patch('services.AdminService.register_student')
    @patch('flask_jwt_extended.view_decorators.verify_jwt_in_request')
    @patch('routes.get_jwt')
    def test_register_student_success(self, mock_get_jwt, mock_verify_jwt, mock_register_student):
        # Mock JWT auth
        mock_get_jwt.return_value = {"role": "admin"}
        mock_verify_jwt.return_value = None
        
        input_data = {
            "name": "New Student",
            "roll_number": "456",
            "email": "new@example.com",
            "course": "CS",
            "password": "password123"
        }
        
        mock_register_student.return_value = {
            "name": "New Student",
            "roll_number": "456",
            "email": "new@example.com",
            "course": "CS",
            "created_at": datetime.now()
        }

        response = self.client.post('/api/students', json=input_data)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['roll_number'], "456")

    @patch('flask_jwt_extended.view_decorators.verify_jwt_in_request')
    @patch('routes.get_jwt')
    def test_register_student_validation_error(self, mock_get_jwt, mock_verify_jwt):
        # Mock JWT auth
        mock_get_jwt.return_value = {"role": "admin"}
        mock_verify_jwt.return_value = None
        
        # Missing password
        input_data = {
            "name": "New Student",
            "roll_number": "456",
            "email": "new@example.com",
            "course": "CS"
        }

        response = self.client.post('/api/students', json=input_data)
        
        self.assertEqual(response.status_code, 422) # Unprocessable Entity
        self.assertIn('errors', response.json)

if __name__ == '__main__':
    unittest.main()
