"""CRUD endpoints for the user-owned Note resource."""
from flask import current_app, request
from flask_restful import Resource
from marshmallow import ValidationError

from auth import error, login_required
from extensions import db
from models import Note
from schemas import flatten_errors, note_schema, notes_schema


def get_owned_note(user, note_id):
    """Fetch a note only if it belongs to ``user``.

    Another user's note and a nonexistent note both give None, so the API
    never confirms that someone else's note id exists (404, not 403).
    """
    return Note.query.filter_by(id=note_id, user_id=user.id).first()


def parse_positive_int(name, default, maximum=None):
    """Read a positive integer query parameter, or raise ValueError."""
    raw = request.args.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{name} must be an integer.")
    if value < 1:
        raise ValueError(f"{name} must be at least 1.")
    return min(value, maximum) if maximum else value


class NoteList(Resource):
    @login_required
    def get(self, user):
        try:
            page = parse_positive_int("page", 1)
            per_page = parse_positive_int(
                "per_page",
                current_app.config["DEFAULT_PER_PAGE"],
                current_app.config["MAX_PER_PAGE"],
            )
        except ValueError as exc:
            return error(str(exc), 400)

        query = (
            db.select(Note)
            .filter_by(user_id=user.id)
            .order_by(Note.created_at.desc(), Note.id.desc())
        )
        # error_out=False: a page past the end returns an empty list, not a 404.
        pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)

        return {
            "items": notes_schema.dump(pagination.items),
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }, 200

    @login_required
    def post(self, user):
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return error("Request body must be a JSON object.", 400)
        try:
            fields = note_schema.load(data)
        except ValidationError as exc:
            return error(flatten_errors(exc), 422)

        # The owner always comes from the session, never from the request body.
        note = Note(user_id=user.id, **fields)
        db.session.add(note)
        db.session.commit()
        return note_schema.dump(note), 201


class NoteDetail(Resource):
    @login_required
    def get(self, user, note_id):
        note = get_owned_note(user, note_id)
        if note is None:
            return error("Note not found.", 404)
        return note_schema.dump(note), 200

    @login_required
    def patch(self, user, note_id):
        note = get_owned_note(user, note_id)
        if note is None:
            return error("Note not found.", 404)

        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return error("Request body must be a JSON object.", 400)
        try:
            fields = note_schema.load(data, partial=True)
        except ValidationError as exc:
            return error(flatten_errors(exc), 422)
        if not fields:
            return error("Provide at least one of: title, content.", 400)

        for key, value in fields.items():
            setattr(note, key, value)
        db.session.commit()
        return note_schema.dump(note), 200

    @login_required
    def delete(self, user, note_id):
        note = get_owned_note(user, note_id)
        if note is None:
            return error("Note not found.", 404)
        db.session.delete(note)
        db.session.commit()
        return "", 204
