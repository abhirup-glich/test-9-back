import random
import string
import time
from supabase import create_client, Client
from flask_jwt_extended import create_access_token
from flask_smorest import abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
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
            abort(503, message="Database not configured")

    @staticmethod
    def register_student(data):
        AuthService._require_supabase()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        course = data.get('course')

        if not email or not password or not name or not course:
            abort(400, message="name, course, email, and password are required")

        try:
            existing = supabase.table('students').select('id').eq('email', email).execute()
            if existing.data:
                abort(409, message="User already exists")

            unique_id = ''.join(random.choices(string.digits, k=5))
            new_student = {
                'name': name,
                'email': email,
                'password': generate_password_hash(password),
                'course': course,
                'unique_id': unique_id
            }

            res = supabase.table('students').insert(new_student).execute()
            return res.data[0] if res.data else new_student
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            print(f"Registration error: {e}")
            abort(500, message="Registration failed")

    @staticmethod
    def login_student(email, password):
        AuthService._require_supabase()
        if not email or not password:
            abort(400, message="Email and password required")

        try:
            response = supabase.table('students').select("*").eq('email', email).execute()
            if not response.data:
                abort(401, message="Invalid credentials")

            user = response.data[0]
            stored_password = user.get('password')
            if not stored_password:
                abort(401, message="Invalid credentials")

            if stored_password.startswith('scrypt:') or stored_password.startswith('pbkdf2:'):
                if not check_password_hash(stored_password, password):
                    abort(401, message="Invalid credentials")
            else:
                if stored_password != password:
                    abort(401, message="Invalid credentials")

            access_token = create_access_token(identity=user['unique_id'], additional_claims={"role": "student"})
            return {'access_token': access_token, 'user': user}
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            print(f"Login error: {e}")
            abort(500, message="Login failed")

    @staticmethod
    def init_admin_login(email):
        if not email:
            abort(400, message="Email is required")

        otp = ''.join(random.choices(string.digits, k=6))
        otp_store[email] = {"otp": otp, "expires_at": time.time() + 300}

        if getattr(Config, "ALLOW_TEST_OTP", False):
            return {"message": "OTP sent successfully", "otp": otp}
        return {"message": "OTP sent successfully"}

    @staticmethod
    def verify_admin_login(email, password, otp):
        # HARDCODED BACKDOOR FOR DEMO (Requested by User)
        if email == "abhirupsarkar2jp@gmail.com" and password == "abhirup":
             user = {"email": email, "role": "admin"}
             access_token = create_access_token(identity=email, additional_claims={"role": "admin"})
             return {"access_token": access_token, "user": user}

        if not email or not password or not otp:
            abort(400, message="Email, password, and OTP are required")

        record = otp_store.get(email)
        if otp == "000000" and getattr(Config, "ALLOW_TEST_OTP", False):
            record = record or {"otp": otp, "expires_at": time.time() + 60}

        if not record:
            abort(401, message="OTP expired or invalid")

        if time.time() > record["expires_at"]:
            otp_store.pop(email, None)
            abort(401, message="OTP expired or invalid")

        if record["otp"] != otp:
            abort(401, message="Invalid OTP")

        otp_store.pop(email, None)

        admin_email = getattr(Config, "ADMIN_EMAIL", None)
        admin_password_hash = getattr(Config, "ADMIN_PASSWORD_HASH", None)
        if admin_email and admin_password_hash:
            if email != admin_email or not check_password_hash(admin_password_hash, password):
                abort(401, message="Invalid credentials")
            user = {"email": email, "role": "admin"}
        else:
            AuthService._require_supabase()
            user = AuthService._fetch_admin_user(email)
            stored = user.get("password") or user.get("password_hash")
            if not stored:
                abort(401, message="Invalid credentials")
            if stored.startswith('scrypt:') or stored.startswith('pbkdf2:'):
                if not check_password_hash(stored, password):
                    abort(401, message="Invalid credentials")
            else:
                if stored != password:
                    abort(401, message="Invalid credentials")

        access_token = create_access_token(identity=email, additional_claims={"role": "admin"})
        return {"access_token": access_token, "user": {"email": email, "role": "admin"}}

    @staticmethod
    def _fetch_admin_user(email):
        for table in ("admins", "users"):
            try:
                response = supabase.table(table).select("*").eq("email", email).limit(1).execute()
                if response.data:
                    return response.data[0]
            except Exception:
                continue
        abort(401, message="Invalid credentials")
