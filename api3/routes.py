from flask_smorest import Blueprint, abort
from flask import jsonify
try:
    from .services import AttendanceService
except ImportError:
    from services import AttendanceService
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
try:
    from .schemas import (
        IdentifyRequestSchema, IdentifyResponseSchema,
        MarkAttendanceRequestSchema, AttendanceRecordSchema
    )
except ImportError:
    from schemas import (
        IdentifyRequestSchema, IdentifyResponseSchema,
        MarkAttendanceRequestSchema, AttendanceRecordSchema
    )

blp = Blueprint('attendance', __name__, description='Attendance operations')

def _require_student_or_admin_for_student_id(student_id):
    claims = get_jwt()
    role = claims.get("role")
    if role == "admin":
        return
    if role == "student" and get_jwt_identity() == student_id:
        return
    abort(403, message="Forbidden")

@blp.route('/api/identify', methods=['POST'])
@blp.arguments(IdentifyRequestSchema)
@blp.response(200, IdentifyResponseSchema)
def identify(data):
    return AttendanceService.identify_user(data['image'])

@blp.route('/api/mark-attendance', methods=['POST'])
@blp.arguments(MarkAttendanceRequestSchema)
@blp.response(201, AttendanceRecordSchema)
@jwt_required()
def mark_attendance(data):
    _require_student_or_admin_for_student_id(data["student_id"])
    return AttendanceService.mark_attendance(data)

@blp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "attendance-service"})
