from marshmallow import Schema, fields, validate

class IdentifyRequestSchema(Schema):
    image = fields.String(required=True)

class IdentifyDataSchema(Schema):
    name = fields.String()
    student_id = fields.String()
    attendance_marked = fields.Boolean()
    confidence = fields.Float()

class IdentifyResponseSchema(Schema):
    status = fields.String()
    data = fields.Nested(IdentifyDataSchema)

class MarkAttendanceRequestSchema(Schema):
    student_id = fields.String(required=True)
    # timestamp can be optional, server time used if missing

class AttendanceRecordSchema(Schema):
    id = fields.Integer(dump_only=True)
    student_id = fields.String()
    name = fields.String()
    time = fields.String()
    status = fields.String()
