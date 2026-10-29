import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from config import TestConfig  # noqa: E402
from extensions import db  # noqa: E402


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def signup(client, username="alice", password="password123"):
    return client.post(
        "/signup",
        json={
            "username": username,
            "password": password,
            "password_confirmation": password,
        },
    )


@pytest.fixture
def alice(client):
    """A client already signed up and logged in as alice."""
    assert signup(client, "alice").status_code == 201
    return client


@pytest.fixture
def bob(app):
    """A second, independent client logged in as bob."""
    c = app.test_client()
    assert signup(c, "bob").status_code == 201
    return c
