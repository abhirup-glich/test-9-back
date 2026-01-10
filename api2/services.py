import random
import string
import time
from supabase import create_client, Client
from flask_jwt_extended import create_access_token
from flask_smorest import abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
import logging

logger = logging.getLogger(__name__)

try:
    from .config import Config
except ImportError:
    from config import Config

def get_supabase_client() -> Client:
    url = Config.SUPABASE_URL
    key = Config.SUPABASE_KEY
    if not url or not key:
        return None
    return create_client(url, key)

supabase = get_supabase_client()

otp_store = {}

class AuthService:
    @staticmethod
    def _require_supabase():
        if supabase is None:
            logger.critical("Supabase client not initialized")
            abort(503, message="Database not configured")
        logger.debug("Supabase client verified")

    @staticmethod
    def register_student(data):
        AuthService._require_supabase()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        course = data.get('course')
        roll_number = data.get('roll_number')

        logger.info(f"Registering student: {email}, Roll: {roll_number}")

        if not email or not password or not name or not course or not roll_number:
            logger.warning("Missing required fields for registration")
            abort(400, message="name, roll_number, course, email, and password are required")

        try:
            # Check for existing email
            logger.debug(f"Checking existing email: {email}")
            existing_email = supabase.table('students').select('id').eq('email', email).execute()
            if existing_email.data:
                logger.warning(f"Email already exists: {email}")
                abort(409, message="User already exists")
            
            # Check for existing roll number
            logger.debug(f"Checking existing roll number: {roll_number}")
            existing_roll = supabase.table('students').select('id').eq('roll_number', roll_number).execute()
            if existing_roll.data:
                logger.warning(f"Roll number already registered: {roll_number}")
                abort(409, message="Roll number already registered")

            new_student = {
                'name': name,
                'email': email,
                'password': password,
                'course': course,
                'roll_number': roll_number
            }

            logger.debug("Inserting new student into Supabase")
            res = supabase.table('students').insert(new_student).execute()
            return res.data[0] if res.data else new_student

        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Registration error: {e}", exc_info=True)
            abort(500, message="Registration failed")

    @staticmethod
    def login_student(email, password):
        AuthService._require_supabase()
        if not email or not password:
            logger.warning("Login attempted without email or password")
            abort(400, message="Email and password required")

        try:
            logger.debug(f"Attempting login for: {email}")
            response = supabase.table('students').select("*").eq('email', email).execute()
            if not response.data:
                logger.warning(f"User not found: {email}")
                abort(401, message="Invalid credentials")

            user = response.data[0]
            stored_password = user.get('password')
            if not stored_password or stored_password != password:
                logger.warning(f"Invalid password for user: {email}")
                abort(401, message="Invalid credentials")

            user_id = user.get('roll_number')
            logger.info(f"Login successful for user: {email}, Roll: {user_id}")
            access_token = create_access_token(identity=user_id, additional_claims={"role": "student"})
            return {'access_token': access_token, 'user': user}
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Login error: {e}", exc_info=True)
            abort(500, message="Login failed")