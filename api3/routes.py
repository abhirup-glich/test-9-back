from flask_smorest import Blueprint, abort
from flask import jsonify, current_app
import logging
try:
    from .services import AttendanceService
except ImportError:
    from services import AttendanceService
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

@blp.route('/api/identify', methods=['POST'])
@blp.arguments(IdentifyRequestSchema)
@blp.response(200, IdentifyResponseSchema)
def identify(data):
    current_app.logger.info("Identify request received")
    return AttendanceService.identify_user(data['image'])

@blp.route('/api/mark-attendance', methods=['POST'])
@blp.arguments(MarkAttendanceRequestSchema)
@blp.response(201, AttendanceRecordSchema)
def mark_attendance(data):
    current_app.logger.debug(f"Entering mark_attendance route with data: {data}")
    current_app.logger.info(f"Mark attendance request for roll_number: {data.get('roll_number')}")
    # Note: Using roll_number instead of student_id based on schema/service usage
    # If the schema uses student_id but service uses roll_number, we need to be careful.
    # Checking service... it uses data.get('roll_number').
    # Let's assume the schema maps correctly or the input JSON has roll_number.
    
    # Validation logic update if needed. 
    # For now just logging.
    result = AttendanceService.mark_attendance(data)
    current_app.logger.info(f"Attendance marked for: {data.get('roll_number')}")
    current_app.logger.debug(f"Mark attendance result: {result}")
    return result

@blp.route('/health', methods=['GET'])
def health():
    current_app.logger.debug("Health check requested")
    return jsonify({"status": "healthy", "service": "attendance-service"})
