"""Marshmallow schemas: input validation and JSON serialization."""
from marshmallow import EXCLUDE, Schema, ValidationError, fields, validate


class UserSchema(Schema):
    """Public representation of a user. No password data is ever included."""

    id = fields.Int(dump_only=True)
    username = fields.Str(dump_only=True)


class NoteSchema(Schema):
    class Meta:
        # Silently drop unknown keys so clients cannot set user_id, id, etc.
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    title = fields.Str(
        required=True, validate=validate.Length(min=1, max=100)
    )
    content = fields.Str(load_default="")
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    user_id = fields.Int(dump_only=True)


user_schema = UserSchema()
note_schema = NoteSchema()
notes_schema = NoteSchema(many=True)


def flatten_errors(err: ValidationError):
    """Turn marshmallow's nested error dict into the flat list the client shows."""
    messages = []
    for field, problems in err.messages.items():
        for problem in problems if isinstance(problems, list) else [problems]:
            messages.append(f"{field}: {problem}")
    return messages
