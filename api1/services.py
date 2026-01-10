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
import logging

logger = logging.getLogger(__name__)

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
            logger.debug("Fetching all students from database")
            response = supabase.table('students').select("*").execute()
            students = response.data
            logger.info(f"Successfully fetched {len(students) if students else 0} students")
            return students
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Error fetching students: {e}", exc_info=True)
            abort(500, message="Failed to fetch students")

    @staticmethod
    def check_attendance():
        AdminService._require_supabase()
        try:
            logger.debug("Fetching attendance records from database")
            # NOTE: This uses 'attendance' table which references students via 'student_id'
            response = supabase.table('attendance').select("*").order('time', desc=True).execute()
            logger.info(f"Successfully fetched {len(response.data) if response.data else 0} attendance records")
            return response.data
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Error checking attendance: {e}", exc_info=True)
            abort(500, message="Failed to fetch attendance")

    @staticmethod
    def register_student(data):
        """
        Registers a new student. Uses roll_number and password keys, aligned with the database.
        """
        AdminService._require_supabase()
        
        roll_number = data['roll_number'].strip()
        email = data['email'].strip().lower()
        logger.debug(f"Attempting to register student: roll={roll_number}, email={email}")
        
        try:
            # --- 1. PRE-INSERT VALIDATION ---
            
            # Check 1: Duplicate Roll Number (Database column: 'roll_number')
            logger.debug(f"Checking for existing roll number: {roll_number}")
            check_uid = supabase.table('students').select('id').eq('roll_number', roll_number).execute()
            if check_uid.data:
                logger.warning(f"Roll number {roll_number} already exists.")
                abort(409, message=f"Roll number {roll_number} is already registered.")

            # Check 2: Duplicate Email (Database column: 'email')
            logger.debug(f"Checking for existing email: {email}")
            existing = supabase.table('students').select('id').eq('email', email).execute()
            if existing.data:
                logger.warning(f"Email {email} already exists.")
                abort(409, message=f"Email {email} is already registered.")

            # --- 2. PREPARE DATA ---

            # Hash the password for security
            password = generate_password_hash(data['password'])
            
            student_data = {
                'name': data['name'],
                'course': data.get('course', ''),
                'email': email,
                'roll_number': roll_number, 
                'password': password # Uses the definitive column name 'password'
            }
            logger.debug(f"Prepared student data for insertion: {student_data}")

            # --- 3. EXECUTE INSERTION ---
            
            logger.debug("Executing insert into students table")
            response = supabase.table('students').insert(student_data).execute()
            
            logger.info(f"Student inserted successfully: {roll_number}")
            return response.data[0] if response.data else student_data
        
        except HTTPException:
            raise
            
        except Exception as e:
            logger.error(f"FATAL Error registering student: {e}", exc_info=True)
            abort(500, message="Failed to register student due to an unexpected server error.")

    @staticmethod
    def update_student(student_id, data):
        AdminService._require_supabase()
        logger.debug(f"Updating student {student_id} with data: {data}")
        if not data:
            logger.warning("Update failed: No data provided")
            abort(400, message="No data provided")

        update_data = {}
        for key in ("name", "course", "email"):
            if key in data and data[key] is not None:
                update_data[key] = data[key]

        # Use confirmed column name 'password'
        if "password" in data and data["password"] is not None:
            update_data["password"] = generate_password_hash(data["password"])

        if not update_data:
            logger.warning("Update failed: No updatable fields provided")
            abort(400, message="No updatable fields provided")

        if "email" in update_data:
            # Simplified email check: only using the confirmed column 'roll_number'
            logger.debug(f"Checking for duplicate email: {update_data['email']}")
            existing = supabase.table('students').select('id,roll_number').eq('email', update_data["email"]).execute()
            
            if existing.data and any(row.get('roll_number') != student_id for row in existing.data):
                logger.warning(f"Email {update_data['email']} already registered to another student")
                abort(409, message="Email already registered")

        try:
            # Simplified update: only using the confirmed column 'roll_number'
            logger.debug(f"Executing update for roll_number: {student_id}")
            response = supabase.table('students').update(update_data).eq('roll_number', student_id).execute()

            if response.data:
                data = response.data[0]
                logger.info(f"Student {student_id} updated successfully")
                return data
            logger.warning(f"Student not found for update: {student_id}")
            abort(404, message="Student not found")
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Error updating student: {e}", exc_info=True)
            abort(500, message="Failed to update student")

    @staticmethod
    def delete_student(student_id):
        AdminService._require_supabase()
        logger.debug(f"Attempting to delete student: {student_id}")
        try:
            # Simplified delete: only using the confirmed column 'roll_number'
            response = supabase.table('students').delete().eq('roll_number', student_id).execute()
            
            if response.data:
                logger.info(f"Student {student_id} deleted successfully")
                return
            logger.warning(f"Student not found for deletion: {student_id}")
            abort(404, message="Student not found")
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Error deleting student: {e}", exc_info=True)
            abort(500, message="Failed to delete student")

    @staticmethod
    def upload_video(file_or_stream, filename=None):
        AdminService._require_supabase()
        try:
            logger.info("Starting video processing")
            if not file_or_stream:
                logger.warning("Video upload failed: No file provided")
                abort(400, message="No file provided")

            # Handle both FileStorage (legacy) and direct stream
            if hasattr(file_or_stream, 'filename') and filename is None:
                filename = file_or_stream.filename
                
            if not filename:
                filename = "unknown_video.webm"
            
            logger.debug(f"Processing video file: {filename}")

            # Process video in memory (Stream processing)
            video_data = file_or_stream.read()
            logger.debug(f"Read {len(video_data)} bytes from video stream")
            
            # Mock result for successful identification
            result_data = {
                "name": "Test Student",
                "roll": "STU001",
                "confidence": 0.98,
                "status": "marked"
            }
            
            logger.info("Video processed successfully (Mock)")

            return {
                "message": "Video processed successfully",
                "filename": filename,
                "data": result_data
            }
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Error processing video: {e}", exc_info=True)
            abort(500, message="Video processing failed")
