import unittest
import os
import json
import logging
import io
import sys
from datetime import datetime

# Adjust path for imports
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from error_manager import ErrorManager, error_manager
    from main import create_app
except ImportError:
    from .error_manager import ErrorManager, error_manager
    from .main import create_app

class TestErrorManager(unittest.TestCase):
    def setUp(self):
        # Capture stderr to verify logging output
        self.captured_stderr = io.StringIO()
        self.original_stderr = sys.stderr
        sys.stderr = self.captured_stderr
        
        # Reset logger handlers to use our captured stream for testing if needed
        # But error_manager writes to sys.stderr directly in log_error
        pass

    def tearDown(self):
        sys.stderr = self.original_stderr
        self.captured_stderr.close()

    def test_log_error_format(self):
        message = "Test error message"
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            error_id = error_manager.log_error(message, exception=e)
        
        output = self.captured_stderr.getvalue()
        
        # Verify format: "[ERROR] [ ${timestamp} ] ${filename} : ${line_number} - ${detailed_error_message} "
        self.assertIn("[ERROR]", output)
        self.assertIn("test_error_system.py", output) # filename
        self.assertIn(message, output)
        self.assertIn("ValueError: Test exception", output)
        
        # Verify error_id is a timestamp
        try:
            # It ends with Z, so remove it for fromisoformat if needed, but it should be fine
            # Python 3.11+ supports Z, earlier might not.
            # error_id is like "2026-01-12T...Z"
            self.assertIn("Z", error_id)
        except ValueError:
            self.fail("error_id is not a valid timestamp string")

    def test_log_error_without_exception(self):
        message = "Simple error"
        error_id = error_manager.log_error(message)
        
        output = self.captured_stderr.getvalue()
        self.assertIn("[ERROR]", output)
        self.assertIn("Simple error", output)
        self.assertIn("test_error_system.py", output)

class TestErrorIntegration(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_404_error_response(self):
        response = self.client.get('/non-existent-route')
        self.assertEqual(response.status_code, 404)
        
        data = response.get_json()
        self.assertIn('error_id', data)
        self.assertIn('timestamp', data)
        self.assertIn('context', data)
        self.assertEqual(data['code'], 404)

if __name__ == '__main__':
    unittest.main()
