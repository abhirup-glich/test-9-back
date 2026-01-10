from marshmallow import Schema, fields, validate

class IdentifyRequestSchema(Schema):
    image = fields.String(required=True)

class IdentifyDataSchema(Schema):
    name = fields.String()
    roll_number = fields.String()
    attendance_marked = fields.Boolean()
    confidence = fields.Float()

class IdentifyResponseSchema(Schema):
    status = fields.String()
    data = fields.Nested(IdentifyDataSchema)

class MarkAttendanceRequestSchema(Schema):
    roll_number = fields.String(required=True)
    # timestamp can be optional, server time used if missing

class AttendanceRecordSchema(Schema):
    id = fields.Integer(dump_only=True)
    roll_number = fields.String()
    name = fields.String()
    time = fields.String()
    status = fields.String()
