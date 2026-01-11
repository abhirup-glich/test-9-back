import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_TITLE = "Admin Service API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.2"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")
    JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY")
    JWT_PUBLIC_KEY_PATH = os.getenv("JWT_PUBLIC_KEY_PATH")
    LOG_JWT_PUBLIC_KEY_ON_ERROR = os.getenv("LOG_JWT_PUBLIC_KEY_ON_ERROR", "false").lower() in ("1", "true", "yes")
    
    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME = os.getenv("DB_NAME", "face_recognition_db")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_USER = os.getenv("DB_USER", "postgres")
    
    # Allow RS256 for Firebase tokens
    JWT_DECODE_ALGORITHMS = ['HS256', 'RS256']
    # Disable signature verification for RS256 since we don't have the dynamic public keys from Firebase
    # WARNING: This is for development/demo only. In production, configure proper key fetching.
    JWT_VERIFY_SIGNATURE = False

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

    @classmethod
    def validate(cls):
        required_vars = [
            "SECRET_KEY", "SUPABASE_URL", "SUPABASE_KEY",
            "DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"
        ]
        missing = [var for var in required_vars if not getattr(cls, var) and not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
