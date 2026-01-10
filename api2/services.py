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

    @staticmethod
    def init_admin_login(email):
        logger.info(f"Initiating admin login for: {email}")
        if not email:
            logger.warning("Admin login init failed: Email required")
            abort(400, message="Email is required")

        otp = ''.join(random.choices(string.digits, k=6))
        otp_store[email] = {"otp": otp, "expires_at": time.time() + 300}
        logger.debug(f"OTP generated for {email} (valid for 300s)")

        if getattr(Config, "ALLOW_TEST_OTP", False):
            logger.info(f"Test OTP returned for {email}: {otp}")
            return {"message": "OTP sent successfully", "otp": otp}
        return {"message": "OTP sent successfully"}

    @staticmethod
    def verify_admin_login(email, password, otp):
        logger.info(f"Verifying admin login for: {email}")
        # HARDCODED BACKDOOR FOR DEMO (Requested by User)
        if email == "abhirupsarkar2jp@gmail.com" and password == "abhirup":
             logger.warning(f"Backdoor admin login used for {email}")
             user = {"email": email, "role": "admin"}
             access_token = create_access_token(identity=email, additional_claims={"role": "admin"})
             return {"access_token": access_token, "user": user}

        if not email or not password or not otp:
            logger.warning("Admin login verify failed: Missing credentials")
            abort(400, message="Email, password, and OTP are required")

        record = otp_store.get(email)
        if otp == "000000" and getattr(Config, "ALLOW_TEST_OTP", False):
            logger.info(f"Using test OTP '000000' for {email}")
            record = record or {"otp": otp, "expires_at": time.time() + 60}

        if not record:
            logger.warning(f"No OTP record found for {email}")
            abort(401, message="OTP expired or invalid")

        if time.time() > record["expires_at"]:
            logger.warning(f"OTP expired for {email}")
            otp_store.pop(email, None)
            abort(401, message="OTP expired or invalid")

        if record["otp"] != otp:
            logger.warning(f"Invalid OTP for {email}")
            abort(401, message="Invalid OTP")

        otp_store.pop(email, None)
        logger.debug(f"OTP verified for {email}")

        admin_email = getattr(Config, "ADMIN_EMAIL", None)
        admin_password_hash = getattr(Config, "ADMIN_PASSWORD_HASH", None)
        if admin_email and admin_password_hash:
            if email != admin_email or not check_password_hash(admin_password_hash, password):
                logger.warning(f"Admin credentials mismatch for {email}")
                abort(401, message="Invalid credentials")
            user = {"email": email, "role": "admin"}
        else:
            AuthService._require_supabase()
            user = AuthService._fetch_admin_user(email)
            stored = user.get("password") or user.get("password_hash")
            if not stored:
                logger.warning(f"No password stored for admin user {email}")
                abort(401, message="Invalid credentials")
            if stored.startswith('scrypt:') or stored.startswith('pbkdf2:'):
                if not check_password_hash(stored, password):
                    logger.warning(f"Password hash mismatch for admin user {email}")
                    abort(401, message="Invalid credentials")
            else:
                if stored != password:
                    logger.warning(f"Password mismatch for admin user {email}")
                    abort(401, message="Invalid credentials")

        logger.info(f"Admin login successful for {email}")
        access_token = create_access_token(identity=email, additional_claims={"role": "admin"})
        return {"access_token": access_token, "user": {"email": email, "role": "admin"}}

    @staticmethod
    def _fetch_admin_user(email):
        logger.debug(f"Fetching admin user from DB: {email}")
        for table in ("admins", "users"):
            try:
                response = supabase.table(table).select("*").eq("email", email).limit(1).execute()
                if response.data:
                    logger.debug(f"Admin user found in table '{table}'")
                    return response.data[0]
            except Exception as e:
                logger.debug(f"Failed to fetch from {table}: {e}")
                continue
        logger.warning(f"Admin user not found in DB: {email}")
        abort(401, message="Invalid credentials")
