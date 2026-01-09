from marshmallow import Schema, fields, validate

class RegisterSchema(Schema):
    name = fields.String(required=True)
    course = fields.String(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=8))

class StudentSchema(Schema):
    id = fields.String(dump_only=True)
    unique_id = fields.String(dump_only=True)
    name = fields.String()
    course = fields.String()
    email = fields.Email()
    created_at = fields.DateTime(dump_only=True)

class AttendanceSchema(Schema):
    id = fields.Integer(dump_only=True)
    student_id = fields.String()
    name = fields.String()
    course = fields.String()
    time = fields.String()
    status = fields.String()
    confidence = fields.Float()

class CheckAttendanceResponseSchema(Schema):
    attendance = fields.List(fields.Nested(AttendanceSchema))

class StudentListResponseSchema(Schema):
    students = fields.List(fields.Nested(StudentSchema))

class UploadResponseSchema(Schema):
    message = fields.String()
    filename = fields.String()
    data = fields.Dict()
