import unittest
from flask import Flask
from datetime import datetime
from main import register_error_handlers
from error_manager import error_manager
from werkzeug.exceptions import BadRequest

class TestConsoleErrors(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        # Ensure error manager is configured (uses default or mock)
        error_manager.configure({})
        register_error_handlers(self.app)
        
        @self.app.route('/trigger-error')
        def trigger_error():
            raise BadRequest("This is a test error for console logging")

        self.client = self.app.test_client()

    def test_error_response_structure(self):
        response = self.client.get('/trigger-error')
        self.assertEqual(response.status_code, 400)
        
        data = response.get_json()
        
        # Check for unique error code
        self.assertIn('error_code', data)
        self.assertIsInstance(data['error_code'], int)
        
        # Check for timestamp
        self.assertIn('timestamp', data)
        # Verify ISO format
        datetime.fromisoformat(data['timestamp'])
        
        # Check for context
        self.assertIn('context', data)
        self.assertIn('url', data['context'])
        self.assertIn('method', data['context'])
        
        # Check message
        self.assertEqual(data['message'], "This is a test error for console logging")

if __name__ == '__main__':
    unittest.main()
