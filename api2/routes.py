from flask_smorest import Blueprint
from flask import jsonify, current_app
import logging
try:
    from .services import AuthService
except ImportError:
    from services import AuthService

try:
    from .schemas import (
        RegisterSchema, LoginSchema, AdminLoginInitSchema,
        AdminLoginVerifySchema, AuthResponseSchema, MessageResponseSchema,
        UserSchema
    )
except ImportError:
    from schemas import (
        RegisterSchema, LoginSchema, AdminLoginInitSchema,
        AdminLoginVerifySchema, AuthResponseSchema, MessageResponseSchema,
        UserSchema
    )

blp = Blueprint('auth', __name__, description='Authentication operations')

@blp.route('/auth/register', methods=['POST'])
@blp.arguments(RegisterSchema)
@blp.response(201, UserSchema)
def register(data):
    current_app.logger.info(f"Register request for: {data.get('email')}")
    result = AuthService.register_student(data)
    current_app.logger.info(f"Successfully registered: {data.get('email')}")
    return result

@blp.route('/auth/login', methods=['POST'])
@blp.arguments(LoginSchema)
@blp.response(200, AuthResponseSchema)
def login(data):
    current_app.logger.debug(f"Entering login route for: {data.get('email')}")
    current_app.logger.info(f"Login request for: {data.get('email')}")
    result = AuthService.login_student(data['email'], data['password'])
    current_app.logger.info(f"Login successful for: {data.get('email')}")
    current_app.logger.debug("Login result returned")
    return result

@blp.route('/auth/admin-login-init', methods=['POST'])
@blp.route('/admin-login-init', methods=['POST'])
@blp.arguments(AdminLoginInitSchema)
@blp.response(200, MessageResponseSchema)
def admin_login_init(data):
    current_app.logger.info(f"Admin login init for: {data.get('email')}")
    return AuthService.init_admin_login(data['email'])

@blp.route('/auth/admin-login-verify', methods=['POST'])
@blp.route('/admin-login-verify', methods=['POST'])
@blp.arguments(AdminLoginVerifySchema)
@blp.response(200, AuthResponseSchema)
def admin_login_verify(data):
    current_app.logger.info(f"Admin login verify for: {data.get('email')}")
    return AuthService.verify_admin_login(data['email'], data['password'], data['otp'])

@blp.route('/health', methods=['GET'])
def health():
    current_app.logger.debug("Health check requested")
    return jsonify({"status": "healthy", "service": "auth-service"})
