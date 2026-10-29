"""Database models: User and the user-owned Note resource."""
from datetime import datetime, timezone

from sqlalchemy.orm import validates

from extensions import bcrypt, db

MIN_PASSWORD_LENGTH = 8


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    _password_hash = db.Column("password_hash", db.String(128), nullable=False)

    notes = db.relationship(
        "Note", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def password_hash(self):
        # The hash is never exposed, even to our own code.
        raise AttributeError("password_hash is not readable")

    @password_hash.setter
    def password_hash(self, password):
        """Hash a plaintext password with bcrypt. Only the hash is stored."""
        if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            )
        self._password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    @validates("username")
    def validate_username(self, _key, username):
        if not isinstance(username, str):
            raise ValueError("Username is required.")
        username = username.strip()
        if not 3 <= len(username) <= 30:
            raise ValueError("Username must be between 3 and 30 characters.")
        return username

    def __repr__(self):
        return f"<User {self.id} {self.username}>"


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )

    user = db.relationship("User", back_populates="notes")

    def __repr__(self):
        return f"<Note {self.id} {self.title!r}>"
