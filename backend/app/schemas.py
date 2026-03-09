from marshmallow import Schema, fields, validate


class HazardReportSchema(Schema):
    hazard_type = fields.Str(required=True)
    route_description = fields.Str(required=True)
    reported_by_number = fields.Str(required=True)
    status = fields.Str(validate=validate.OneOf(["ACTIVE", "UNVERIFIED", "CLEARED"]), load_default="UNVERIFIED")


class JobCreateSchema(Schema):
    caller_number = fields.Str(required=True)
    village_code = fields.Str(required=True)
    emergency_type = fields.Str(required=True, validate=validate.OneOf(["MATERNITY", "INJURY", "OTHER"]))


class RiderCheckinSchema(Schema):
    stage_code = fields.Str(required=True)


class ClaimJobSchema(Schema):
    rider_phone = fields.Str(required=True)
