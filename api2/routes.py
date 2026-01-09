from flask_smorest import Blueprint
from flask import jsonify
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
    return AuthService.register_student(data)

@blp.route('/auth/login', methods=['POST'])
@blp.arguments(LoginSchema)
@blp.response(200, AuthResponseSchema)
def login(data):
    return AuthService.login_student(data['email'], data['password'])

@blp.route('/auth/admin-login-init', methods=['POST'])
@blp.route('/admin-login-init', methods=['POST'])
@blp.arguments(AdminLoginInitSchema)
@blp.response(200, MessageResponseSchema)
def admin_login_init(data):
    return AuthService.init_admin_login(data['email'])

@blp.route('/auth/admin-login-verify', methods=['POST'])
@blp.route('/admin-login-verify', methods=['POST'])
@blp.arguments(AdminLoginVerifySchema)
@blp.response(200, AuthResponseSchema)
def admin_login_verify(data):
    return AuthService.verify_admin_login(data['email'], data['password'], data['otp'])

@blp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "auth-service"})
