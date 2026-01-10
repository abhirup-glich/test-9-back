from supabase import create_client, Client
try:
    from .config import Config
except ImportError:
    from config import Config
from flask_smorest import abort
from datetime import datetime, timezone
from werkzeug.exceptions import HTTPException

def get_supabase_client() -> Client:
    url = Config.SUPABASE_URL
    key = Config.SUPABASE_KEY
    if not url or not key:
        return None
    return create_client(url, key)

supabase = get_supabase_client()

class AttendanceService:
    @staticmethod
    def _require_supabase():
        if supabase is None:
            abort(503, message="Database not configured")

    @staticmethod
    def identify_user(image_data):
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
        AttendanceService._require_supabase()
        roll_number = data.get('roll_number')
        if not roll_number:
            abort(400, message="Roll number required")

        try:
            student = supabase.table('students').select('name,course,roll_number').eq('roll_number', roll_number).execute()

            if not student.data:
                abort(404, message="Student not found")

            record = {
                "roll_number": roll_number,
                "time": datetime.now(timezone.utc).isoformat(),
                "status": "present",
                "name": student.data[0].get("name") or "Unknown",
                "course": student.data[0].get("course")
            }

            response = supabase.table('attendance').insert(record).execute()
            return response.data[0] if response.data else record

        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            print(f"Error marking attendance: {e}")
            abort(500, message="Failed to mark attendance")
