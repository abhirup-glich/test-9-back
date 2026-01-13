import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import sys
import os

# Add the directory to path to import logic
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock dependencies before importing logic
sys.modules['cv2'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['facenet_pytorch'] = MagicMock()

# Now import logic
import logic

class TestRegisterStudentWeb(unittest.TestCase):
    def setUp(self):
        self.mock_cur = MagicMock()
        self.mock_conn = MagicMock()
        
        # Setup mock for process_web_image
        self.original_process_web_image = logic.process_web_image
        logic.process_web_image = MagicMock()
        
    def tearDown(self):
        logic.process_web_image = self.original_process_web_image

    def test_register_student_success(self):
        # Mock embeddings
        logic.process_web_image.side_effect = [
            np.array([0.1]*512), # center
            np.array([0.2]*512), # left
            np.array([0.3]*512)  # right
        ]
        
        images = {
            'center': 'base64data',
            'left': 'base64data',
            'right': 'base64data'
        }
        
        result = logic.register_student_web(
            self.mock_cur, 
            "TEST001", 
            "Test Student", 
            "CS101", 
            images
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('registered successfully', result['message'])
        self.mock_cur.execute.assert_called_once()
        
    def test_register_student_missing_face(self):
        # Mock embedding return None for center
        logic.process_web_image.return_value = None
        
        images = {'center': 'base64data'}
        
        result = logic.register_student_web(
            self.mock_cur, 
            "TEST001", 
            "Test Student", 
            "CS101", 
            images
        )
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Face not detected', result['message'])

    def test_register_student_single_image(self):
        # Mock embeddings (center used for all)
        logic.process_web_image.side_effect = [
            np.array([0.1]*512), # center -> center
            np.array([0.1]*512), # center -> left
            np.array([0.1]*512)  # center -> right
        ]
        
        images = {'center': 'base64data'}
        
        result = logic.register_student_web(
            self.mock_cur, 
            "TEST001", 
            "Test Student", 
            "CS101", 
            images
        )
        
        self.assertEqual(result['status'], 'success')
        # Check if left and right were populated
        self.assertIn('left', images)
        self.assertIn('right', images)

if __name__ == '__main__':
    unittest.main()
