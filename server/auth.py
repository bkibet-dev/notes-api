"""Authentication helpers shared by all protected resources."""
from functools import wraps

from flask import session

from extensions import db
from models import User


def error(messages, status):
    """Build a JSON error response in the shape the frontend expects."""
    if isinstance(messages, str):
        messages = [messages]
    return {"errors": messages}, status


def current_user():
    """Return the logged-in User, or None. Clears stale session ids."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    user = db.session.get(User, user_id)
    if user is None:
        # The user was deleted after the cookie was issued.
        session.pop("user_id", None)
    return user


def login_required(view):
    """Reject the request with 401 unless a valid user is logged in.

    The authenticated user is passed to the view as its first argument after
    ``self``, so views never need to trust an id supplied by the client.
    """

    @wraps(view)
    def wrapper(self, *args, **kwargs):
        user = current_user()
        if user is None:
            return error("Unauthorized. Please log in.", 401)
        return view(self, user, *args, **kwargs)

    return wrapper
