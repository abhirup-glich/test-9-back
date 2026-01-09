from supabase import create_client, Client
try:
    from .config import Config
except ImportError:
    from config import Config
import random
import string
from flask_smorest import abort
from werkzeug.security import generate_password_hash
from werkzeug.exceptions import HTTPException

def get_supabase_client() -> Client:
    url = Config.SUPABASE_URL
    key = Config.SUPABASE_KEY
    if not url or not key:
        return None
    return create_client(url, key)

supabase = get_supabase_client()

class AdminService:
    @staticmethod
    def _require_supabase():
        if supabase is None:
            abort(503, message="Database not configured")

    @staticmethod
    def get_all_students():
        AdminService._require_supabase()
        try:
            response = supabase.table('students').select("*").execute()
            return response.data
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            print(f"Error fetching students: {e}")
            abort(500, message="Failed to fetch students")

    @staticmethod
    def check_attendance():
        AdminService._require_supabase()
        try:
            response = supabase.table('attendance').select("*").order('time', desc=True).execute()
            return response.data
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            print(f"Error checking attendance: {e}")
            abort(500, message="Failed to fetch attendance")

    @staticmethod
    def register_student(data):
        AdminService._require_supabase()
        unique_id = ''.join(random.choices(string.digits, k=5))

        try:
            existing = supabase.table('students').select('id').eq('email', data['email']).execute()
            if existing.data:
                abort(409, message="Email already registered")

            student_data = {
                'name': data['name'],
                'course': data.get('course', ''),
                'email': data['email'],
                'unique_id': unique_id,
                'password': generate_password_hash(data['password'])
            }

            response = supabase.table('students').insert(student_data).execute()
            return response.data[0] if response.data else student_data
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            print(f"Error registering student: {e}")
            abort(500, message=f"Failed to register student: {str(e)}")

    @staticmethod
    def update_student(student_id, data):
        AdminService._require_supabase()
        if not data:
            abort(400, message="No data provided")

        update_data = {}
        for key in ("name", "course", "email"):
            if key in data and data[key] is not None:
                update_data[key] = data[key]

        if "password" in data and data["password"] is not None:
            update_data["password"] = generate_password_hash(data["password"])

        if not update_data:
            abort(400, message="No updatable fields provided")

        if "email" in update_data:
            existing = supabase.table('students').select('id,unique_id').eq('email', update_data["email"]).execute()
            if existing.data and any(row.get("unique_id") != student_id for row in existing.data):
                abort(409, message="Email already registered")

        try:
            response = supabase.table('students').update(update_data).eq('unique_id', student_id).execute()
            if response.data:
                return response.data[0]
            abort(404, message="Student not found")
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            print(f"Error updating student: {e}")
            abort(500, message="Failed to update student")

    @staticmethod
    def delete_student(student_id):
        AdminService._require_supabase()
        try:
            response = supabase.table('students').delete().eq('unique_id', student_id).execute()
            if response.data:
                return
            abort(404, message="Student not found")
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            print(f"Error deleting student: {e}")
            abort(500, message="Failed to delete student")

    @staticmethod
    def upload_video(file_or_stream, filename=None):
        AdminService._require_supabase()
        try:
            if not file_or_stream:
                abort(400, message="No file provided")

            # Handle both FileStorage (legacy) and direct stream
            if hasattr(file_or_stream, 'filename') and filename is None:
                filename = file_or_stream.filename
            
            if not filename:
                filename = "unknown_video.webm"

            # Process video in memory (Stream processing)
            # Task 4: In-memory processing, no file system writes
            video_data = file_or_stream.read()
            
            # Simulate processing time or logic
            # In a real implementation, this would pass 'video_data' to a face recognition service
            
            # Mock result for successful identification
            result_data = {
                "name": "Test Student",
                "roll": "STU001",
                "confidence": 0.98,
                "status": "marked"
            }

            return {
                "message": "Video processed successfully",
                "filename": filename,
                "data": result_data
            }
        except Exception as e:
             if isinstance(e, HTTPException):
                 raise
             print(f"Error processing video: {e}")
             abort(500, message="Video processing failed")
