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
    
    # Allow RS256 for Firebase tokens
    JWT_DECODE_ALGORITHMS = ['HS256', 'RS256']
    # Disable signature verification for RS256 since we don't have the dynamic public keys from Firebase
    # WARNING: This is for development/demo only. In production, configure proper key fetching.
    JWT_VERIFY_SIGNATURE = False

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
