from conftest import signup
from extensions import db
from models import User


def test_signup_creates_user_and_logs_in(client):
    r = signup(client)
    assert r.status_code == 201
    assert r.get_json()["username"] == "alice"
    assert "password" not in str(r.get_json())
    assert client.get("/check_session").status_code == 200


def test_password_is_hashed(client):
    signup(client)
    user = User.query.filter_by(username="alice").first()
    assert user._password_hash != "password123"
    assert user._password_hash.startswith("$2")
    assert user.authenticate("password123")
    assert not user.authenticate("wrong")


def test_password_hash_not_readable():
    import pytest
    with pytest.raises(AttributeError):
        User(username="abc").password_hash


def test_signup_duplicate_username_is_409(client):
    signup(client)
    assert signup(client).status_code == 409


def test_signup_validation(client):
    r = client.post("/signup", json={"username": "al", "password": "password123",
                                     "password_confirmation": "password123"})
    assert r.status_code == 422
    r = client.post("/signup", json={"username": "alice", "password": "short",
                                     "password_confirmation": "short"})
    assert r.status_code == 422
    r = client.post("/signup", json={"username": "alice", "password": "password123",
                                     "password_confirmation": "different"})
    assert r.status_code == 422
    assert "errors" in r.get_json()
    assert client.post("/signup").status_code == 422
    assert db.session.query(User).count() == 0


def test_login_success_and_failure(app):
    signup(app.test_client())
    c = app.test_client()
    assert c.get("/check_session").status_code == 401
    assert c.post("/login", json={"username": "alice", "password": "nope"}).status_code == 401
    assert c.post("/login", json={"username": "ghost", "password": "x"}).status_code == 401
    assert c.post("/login", json={}).status_code == 401
    r = c.post("/login", json={"username": "alice", "password": "password123"})
    assert r.status_code == 200
    assert set(r.get_json()) == {"id", "username"}
    assert c.get("/check_session").get_json()["username"] == "alice"


def test_check_session_logged_out_is_401_with_empty_body(client):
    r = client.get("/check_session")
    assert r.status_code == 401
    assert r.get_json() == {}


def test_logout(alice):
    assert alice.delete("/logout").status_code == 204
    assert alice.get("/check_session").status_code == 401
    assert alice.get("/notes").status_code == 401
