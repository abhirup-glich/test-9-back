from flask_smorest import Blueprint, abort
from flask import request, jsonify, current_app
try:
    from .services import AdminService
except ImportError:
    from services import AdminService
import logging

# ... imports ...
try:
    from .schemas import (
        CheckAttendanceResponseSchema,
        StudentListResponseSchema,
        RegisterSchema,
        StudentSchema,
        UploadResponseSchema
    )
except ImportError:
    from schemas import (
        CheckAttendanceResponseSchema,
        StudentListResponseSchema,
        RegisterSchema,
        StudentSchema,
        UploadResponseSchema
    )
blp = Blueprint('admin', __name__, description='Admin operations')

@blp.route('/api/check_attendance', methods=['GET'])
@blp.route('/check_attendance', methods=['GET'])
@blp.response(200, CheckAttendanceResponseSchema)
def check_attendance():
    current_app.logger.debug("Entering check_attendance route")
    current_app.logger.info("Received request to check attendance")
    result = AdminService.check_attendance()
    current_app.logger.info(f"Returning {len(result)} attendance records")
    current_app.logger.debug(f"Check attendance result: {result}")
    return {"attendance": result}

@blp.route('/api/students', methods=['GET'])
@blp.route('/students', methods=['GET'])
@blp.response(200, StudentListResponseSchema)
def get_students():
    current_app.logger.info("Received request to fetch all students")
    result = AdminService.get_all_students()
    current_app.logger.info(f"Returning {len(result)} students")
    return {"students": result}

@blp.route('/api/students', methods=['POST'])
@blp.route('/register_student', methods=['POST'])
@blp.arguments(RegisterSchema)
@blp.response(201, StudentSchema)
def register_student(data):
    current_app.logger.info(f"Received request to register student: {data.get('email')}")
    result = AdminService.register_student(data)
    current_app.logger.info(f"Student registered successfully: {result.get('roll_number')}")
    return result

@blp.route('/api/students/<student_id>', methods=['PUT'])
@blp.route('/students/<student_id>', methods=['PUT'])
@blp.arguments(RegisterSchema(partial=True))
@blp.response(200, StudentSchema)
def update_student(data, student_id):
    current_app.logger.info(f"Received request to update student {student_id}")
    result = AdminService.update_student(student_id, data)
    current_app.logger.info(f"Student {student_id} updated successfully")
    return result

@blp.route('/api/students/<student_id>', methods=['DELETE'])
@blp.route('/students/<student_id>', methods=['DELETE'])
@blp.response(204, None)
def delete_student(student_id):
    current_app.logger.debug(f"Entering delete_student route for {student_id}")
    current_app.logger.info(f"Received request to delete student {student_id}")
    AdminService.delete_student(student_id)
    current_app.logger.info(f"Student {student_id} deleted successfully")
    current_app.logger.debug(f"Deletion completed for {student_id}")
    return "", 204

@blp.route('/api/upload', methods=['POST'])
@blp.route('/upload', methods=['POST'])
@blp.response(200, UploadResponseSchema)
def upload_video():
    current_app.logger.debug("Entering upload_video route")
    current_app.logger.info("Received video upload request")
    _require_admin()
    
    # Handle direct stream upload (Task 2 & 4)
    if request.content_type == 'video/webm':
        filename = request.headers.get('X-Filename', 'video.webm')
        current_app.logger.info(f"Processing stream upload: {filename}")
        current_app.logger.debug(f"Stream upload details: {filename}")
        # Pass the raw stream
        return AdminService.upload_video(request.stream, filename=filename)

    if 'video' not in request.files:
        current_app.logger.error("No video file part in request")
        abort(400, message="No video file part")
    file = request.files['video']
    current_app.logger.info(f"Processing file upload: {file.filename}")
    current_app.logger.debug(f"File upload details: {file.filename}")
    return AdminService.upload_video(file)

@blp.route('/health', methods=['GET'])
def health():
    current_app.logger.debug("Health check requested")
    return jsonify({"status": "healthy", "service": "admin-service"})
