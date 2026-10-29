"""Signup, login, session check and logout endpoints."""
from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from auth import current_user, error
from extensions import db
from models import User
from schemas import user_schema


def start_session(user):
    """Log a user in. Clearing first prevents session fixation."""
    session.clear()
    session["user_id"] = user.id
    session.permanent = True


class Signup(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        username = data.get("username")
        password = data.get("password")

        errors = []
        if not username:
            errors.append("Username is required.")
        if not password:
            errors.append("Password is required.")
        elif password != data.get("password_confirmation"):
            errors.append("Password confirmation does not match.")
        if errors:
            return error(errors, 422)

        try:
            user = User(username=username)
            user.password_hash = password
            db.session.add(user)
            db.session.commit()
        except ValueError as exc:
            db.session.rollback()
            return error(str(exc), 422)
        except IntegrityError:
            # The unique constraint on username is the source of truth, which
            # also covers two simultaneous signups.
            db.session.rollback()
            return error("Username is already taken.", 409)

        start_session(user)
        return user_schema.dump(user), 201


class Login(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        user = User.query.filter_by(username=username).first()
        # Same message for unknown user and wrong password, so the API does
        # not reveal which usernames exist.
        if user is None or not user.authenticate(password):
            return error("Invalid username or password.", 401)

        start_session(user)
        return user_schema.dump(user), 200


class CheckSession(Resource):
    def get(self):
        user = current_user()
        if user is None:
            # Must not be a 2xx: the client treats any ok response as "logged in".
            return {}, 401
        return user_schema.dump(user), 200


class Logout(Resource):
    def delete(self):
        session.clear()
        return "", 204
