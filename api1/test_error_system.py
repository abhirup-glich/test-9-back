import unittest
import os
import json
import threading
from flask import Flask
from werkzeug.exceptions import NotFound, InternalServerError

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
        # Use a temporary file for testing
        self.test_file = 'test_error_counters.json'
        # Reset the singleton for testing purposes (hacky but needed for clean state)
        # Since ErrorManager is a singleton, we might need to manually reset it or just create a new instance bypassing singleton if possible.
        # However, the class uses __new__ for singleton.
        # We will just manually instantiate a new one by modifying the persistence file path of the global one 
        # OR better, creating a subclass or just handling the global state.
        
        # Let's just create a new instance using the class logic if we can reset the singleton, 
        # or just modify the global instance's file.
        error_manager.persistence_file = self.test_file
        error_manager.counters = {}
        error_manager.save_counters()

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_increment_logic(self):
        # Test 500 -> 501
        code1 = error_manager.get_next_code(500)
        self.assertEqual(code1, 500)
        
        code2 = error_manager.get_next_code(500)
        self.assertEqual(code2, 501)
        
        code3 = error_manager.get_next_code(500)
        self.assertEqual(code3, 502)

        # Test distinct counters for different types
        code_404_1 = error_manager.get_next_code(404)
        self.assertEqual(code_404_1, 404)
        
        code_404_2 = error_manager.get_next_code(404)
        self.assertEqual(code_404_2, 405)
        
        # Ensure 500 sequence wasn't affected
        code4 = error_manager.get_next_code(500)
        self.assertEqual(code4, 503)

    def test_persistence(self):
        # Generate some codes
        error_manager.get_next_code(500) # 500
        error_manager.get_next_code(500) # 501
        
        # Verify file content
        with open(self.test_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(data['500'], 501)
            
        # Simulate restart by clearing memory and reloading
        error_manager.counters = {}
        error_manager.load_counters()
        
        # Next code should be 502
        code = error_manager.get_next_code(500)
        self.assertEqual(code, 502)

    def test_concurrency(self):
        def worker():
            for _ in range(100):
                error_manager.get_next_code(500)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        
        # Reset counter to known state
        error_manager.counters['500'] = 499 
        # so first call makes it 500. 
        # Wait, get_next_code logic: if not exists, set to base. If exists, increment.
        # If I want to test 1000 increments.
        error_manager.counters = {'500': 500} # Start at 500 (so next is 501)
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
            
        # 10 threads * 100 increments = 1000 increments.
        # Started at 500. Should end at 1500.
        self.assertEqual(error_manager.counters['500'], 500 + 1000)

class TestErrorIntegration(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Point error manager to test file
        error_manager.persistence_file = 'test_integration_counters.json'
        error_manager.counters = {}

    def tearDown(self):
        if os.path.exists('test_integration_counters.json'):
            os.remove('test_integration_counters.json')

    def test_404_error_code(self):
        # Trigger 404
        response = self.client.get('/non-existent-route')
        self.assertEqual(response.status_code, 404)
        
        data = response.get_json()
        self.assertIn('error_code', data)
        self.assertEqual(data['error_code'], 404)
        
        # Second 404
        response = self.client.get('/non-existent-route-2')
        data = response.get_json()
        self.assertEqual(data['error_code'], 405)

if __name__ == '__main__':
    unittest.main()
