from supabase import create_client, Client, ClientOptions
from flask import request
try:
    from .config import Config
except ImportError:
    from config import Config
from flask_smorest import abort
from datetime import datetime, timezone
from werkzeug.exceptions import HTTPException
import logging

logger = logging.getLogger(__name__)

def get_supabase() -> Client:
    url = Config.SUPABASE_URL
    key = Config.SUPABASE_KEY
    if not url or not key:
        return None
    
    headers = {}
    auth_header = request.headers.get('Authorization')
    if auth_header:
        headers['Authorization'] = auth_header
    
    return create_client(url, key, options=ClientOptions(headers=headers))

class AttendanceService:
    @staticmethod
    def _get_client():
        client = get_supabase()
        if client is None:
            logger.critical("Supabase client not initialized")
            abort(503, message="Database not configured")
        return client

    @staticmethod
    def identify_user(image_data):
        logger.info("Identifying user from image data")
        # Placeholder implementation
        return {
            "status": "success",
            "data": {
                "name": "Abhirup",
                "roll_number": "STU12345",
                "attendance_marked": True,
                "confidence": 0.98
            }
        }

    @staticmethod
    def mark_attendance(data):
        supabase = AttendanceService._get_client()
        roll_number = data.get('roll_number')
        
        logger.info(f"Marking attendance for roll_number: {roll_number}")
        
        if not roll_number:
            logger.warning("Roll number missing in request")
            abort(400, message="Roll number required")

        try:
            logger.debug(f"Verifying student exists: {roll_number}")
            student = supabase.table('students').select('name,course,roll_number').eq('roll_number', roll_number).execute()

            if not student.data:
                logger.warning(f"Student not found: {roll_number}")
                abort(404, message="Student not found")

            record = {
                "roll_number": roll_number,
                "time": datetime.now(timezone.utc).isoformat(),
                "status": "present",
                "name": student.data[0].get("name") or "Unknown",
                "course": student.data[0].get("course")
            }

            logger.debug("Inserting attendance record")
            response = supabase.table('attendance').insert(record).execute()
            
            logger.info(f"Attendance marked successfully for {roll_number}")
            return response.data[0] if response.data else record

        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Error marking attendance: {e}", exc_info=True)
            abort(500, message="Failed to mark attendance")
