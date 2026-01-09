from flask_smorest import Blueprint, abort
from flask import request, jsonify
try:
    from .services import AdminService
except ImportError:
    from services import AdminService
from flask_jwt_extended import jwt_required, get_jwt
try:
    from .schemas import (
        RegisterSchema, StudentSchema, AttendanceSchema,
        StudentListResponseSchema, CheckAttendanceResponseSchema,
        UploadResponseSchema
    )
except ImportError:
    from schemas import (
        RegisterSchema, StudentSchema, AttendanceSchema,
        StudentListResponseSchema, CheckAttendanceResponseSchema,
        UploadResponseSchema
    )

blp = Blueprint('admin', __name__, description='Admin operations')

def _require_admin():
    claims = get_jwt()
    if claims.get("role") != "admin":
        abort(403, message="Forbidden")

@blp.route('/api/check_attendance', methods=['GET'])
@blp.route('/check_attendance', methods=['GET'])
@blp.response(200, CheckAttendanceResponseSchema)
@jwt_required()
def check_attendance():
    _require_admin()
    return {"attendance": AdminService.check_attendance()}

@blp.route('/api/students', methods=['GET'])
@blp.route('/students', methods=['GET'])
@blp.response(200, StudentListResponseSchema)
@jwt_required()
def get_students():
    _require_admin()
    return {"students": AdminService.get_all_students()}

@blp.route('/api/students', methods=['POST'])
@blp.route('/register_student', methods=['POST'])
@blp.arguments(RegisterSchema)
@blp.response(201, StudentSchema)
@jwt_required()
def register_student(data):
    _require_admin()
    return AdminService.register_student(data)

@blp.route('/api/students/<student_id>', methods=['PUT'])
@blp.route('/students/<student_id>', methods=['PUT'])
@blp.arguments(RegisterSchema(partial=True))
@blp.response(200, StudentSchema)
@jwt_required()
def update_student(data, student_id):
    _require_admin()
    return AdminService.update_student(student_id, data)

@blp.route('/api/students/<student_id>', methods=['DELETE'])
@blp.route('/students/<student_id>', methods=['DELETE'])
@blp.response(204, None)
@jwt_required()
def delete_student(student_id):
    _require_admin()
    AdminService.delete_student(student_id)
    return "", 204

@blp.route('/api/upload', methods=['POST'])
@blp.route('/upload', methods=['POST'])
@blp.response(200, UploadResponseSchema)
@jwt_required()
def upload_video():
    _require_admin()
    
    # Handle direct stream upload (Task 2 & 4)
    if request.content_type == 'video/webm':
        filename = request.headers.get('X-Filename', 'video.webm')
        # Pass the raw stream
        return AdminService.upload_video(request.stream, filename=filename)

    if 'video' not in request.files:
        abort(400, message="No video file part")
    file = request.files['video']
    return AdminService.upload_video(file)

@blp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "admin-service"})
