from flask import request, jsonify
from flask_smorest import Blueprint
import logging
try:
    from .logic import register_student_web, connect_db, delete_last_attendance, setup_db
except ImportError:
    from logic import register_student_web, connect_db, delete_last_attendance, setup_db

blp = Blueprint('face_ops', __name__, description='Face Recognition Operations')
logger = logging.getLogger(__name__)

@blp.route('/register_student', methods=['POST'])
def register_student():
    return register_student_impl()

@blp.route('/api/register_student', methods=['POST'])
def api_register_student():
    return register_student_impl()

def register_student_impl():
    try:
        data = request.json
        roll = data.get('roll')
        name = data.get('name')
        course = data.get('course')
        images = data.get('images') # Expects {center: '...', left: '...', right: '...'}
        
        if not all([roll, name, course, images]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        conn, cur = connect_db()
        # Ensure table structure exists (optional, could be done at startup)
        # from logic import setup_db; setup_db(cur) 
        
        result = register_student_web(cur, roll, name, course, images)
        conn.close()
        
        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Registration failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@blp.route('/delete_last_attendance', methods=['POST'])
def delete_last_attendance_route():
    return delete_last_attendance_impl()

def delete_last_attendance_impl():
    try:
        conn, cur = connect_db()
        deleted = delete_last_attendance(cur)
        conn.close()
        
        if deleted:
            return jsonify({
                'status': 'success',
                'message': f"Deleted attendance for {deleted['name']} at {deleted['time']}"
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No attendance record found to delete'
            }), 404
            
    except Exception as e:
        logger.error(f"Delete attendance failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
