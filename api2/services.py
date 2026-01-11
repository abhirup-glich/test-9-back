import random
import string
import time
from supabase import create_client, Client, ClientOptions
from flask import request
from flask_smorest import abort
from werkzeug.exceptions import HTTPException
import logging

logger = logging.getLogger(__name__)

try:
    from .config import Config
except ImportError:
    from config import Config

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

otp_store = {}

class AuthService:
    @staticmethod
    def _get_client():
        client = get_supabase()
        if client is None:
            logger.critical("Supabase client not initialized")
            abort(503, message="Database not configured")
        return client

    @staticmethod
    def register_student(data):
        supabase = AuthService._get_client()
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
            # 1. Sign up with Supabase Auth (GoTrue)
            # This creates the user in auth.users and returns a session
            logger.debug(f"Creating Supabase Auth user: {email}")
            auth_res = supabase.auth.sign_up({
                "email": email, 
                "password": password,
                "options": {
                    "data": {
                        "name": name,
                        "roll_number": roll_number,
                        "course": course
                    }
                }
            })
            
            # If sign up successful, we also insert into 'students' table for backward compatibility/metadata
            # But wait, if RLS is on, anon might not be able to insert into students?
            # Unless we have a trigger on auth.users -> students.
            # Assuming we need to manually insert for now.
            
            # Check for existing email in students table (legacy check)
            existing_email = supabase.table('students').select('id').eq('email', email).execute()
            if existing_email.data:
                 logger.warning(f"Email already exists in students table: {email}")
                 # Proceeding might be okay if auth.sign_up succeeded, but it implies sync issue.
            
            # Insert into students table
            # We hash password for students table as it expects it (legacy), 
            # even though Supabase Auth handles the real password.
            from werkzeug.security import generate_password_hash
            hashed_pw = generate_password_hash(password)
            
            new_student = {
                'name': name,
                'email': email,
                'password': hashed_pw,
                'course': course,
                'roll_number': roll_number
            }

            logger.debug("Inserting new student into Supabase students table")
            res = supabase.table('students').insert(new_student).execute()
            
            # Return user data (from auth response or students table)
            # Returning students table data to match schema
            return res.data[0] if res.data else new_student

        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Registration error: {e}", exc_info=True)
            # Map Supabase Auth errors
            abort(400, message=str(e))

    @staticmethod
    def login_student(email, password):
        supabase = AuthService._get_client()
        if not email or not password:
            logger.warning("Login attempted without email or password")
            abort(400, message="Email and password required")

        try:
            logger.debug(f"Attempting Supabase Auth login for: {email}")
            # Use Supabase Auth to sign in
            session = supabase.auth.sign_in_with_password({"email": email, "password": password})
            
            # Return the access token and user info
            # We need to format this to match what the frontend expects.
            # Frontend likely expects {access_token: ..., user: ...}
            
            return {
                "access_token": session.session.access_token,
                "refresh_token": session.session.refresh_token,
                "user": {
                    "id": session.user.id,
                    "email": session.user.email,
                    # Add extra fields if needed, fetched from students table or metadata
                    "name": session.user.user_metadata.get('name'),
                    "roll_number": session.user.user_metadata.get('roll_number')
                }
            }

        except Exception as e:
            logger.warning(f"Login failed for {email}: {e}")
            abort(401, message="Invalid credentials")