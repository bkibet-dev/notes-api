import pytest

ROUTES = [
    ("get", "/notes"),
    ("post", "/notes"),
    ("get", "/notes/1"),
    ("patch", "/notes/1"),
    ("delete", "/notes/1"),
]


@pytest.mark.parametrize("method,url", ROUTES)
def test_all_note_routes_require_login(client, method, url):
    r = getattr(client, method)(url, json={"title": "x"})
    assert r.status_code == 401
    assert "errors" in r.get_json()


def test_create_and_read(alice):
    r = alice.post("/notes", json={"title": "Groceries", "content": "milk"})
    assert r.status_code == 201
    note = r.get_json()
    assert note["title"] == "Groceries" and note["user_id"] == 1
    assert alice.get(f"/notes/{note['id']}").get_json()["content"] == "milk"


def test_create_validation(alice):
    assert alice.post("/notes", json={}).status_code == 422
    assert alice.post("/notes", json={"title": ""}).status_code == 422
    assert alice.post("/notes", json={"title": "x" * 101}).status_code == 422
    assert alice.post("/notes", data="not json").status_code == 400
    assert alice.post("/notes", json=[1]).status_code == 400


def test_client_cannot_set_owner(alice, bob):
    r = alice.post("/notes", json={"title": "mine", "user_id": 2})
    assert r.get_json()["user_id"] == 1
    assert bob.get("/notes").get_json()["total"] == 0


def test_patch_partial_and_validation(alice):
    nid = alice.post("/notes", json={"title": "a", "content": "b"}).get_json()["id"]
    r = alice.patch(f"/notes/{nid}", json={"content": "new"})
    assert r.status_code == 200
    assert r.get_json()["title"] == "a" and r.get_json()["content"] == "new"
    assert alice.patch(f"/notes/{nid}", json={}).status_code == 400
    assert alice.patch(f"/notes/{nid}", json={"title": ""}).status_code == 422
    assert alice.patch(f"/notes/{nid}", json={"user_id": 99}).status_code == 400


def test_delete(alice):
    nid = alice.post("/notes", json={"title": "a"}).get_json()["id"]
    assert alice.delete(f"/notes/{nid}").status_code == 204
    assert alice.get(f"/notes/{nid}").status_code == 404
    assert alice.delete(f"/notes/{nid}").status_code == 404


def test_users_cannot_touch_each_others_notes(alice, bob):
    nid = alice.post("/notes", json={"title": "secret", "content": "x"}).get_json()["id"]
    assert bob.get(f"/notes/{nid}").status_code == 404
    assert bob.patch(f"/notes/{nid}", json={"title": "hacked"}).status_code == 404
    assert bob.delete(f"/notes/{nid}").status_code == 404
    assert bob.get("/notes").get_json()["items"] == []
    # Alice's note is untouched.
    assert alice.get(f"/notes/{nid}").get_json()["title"] == "secret"


def test_pagination(alice):
    for i in range(25):
        alice.post("/notes", json={"title": f"n{i}"})

    r = alice.get("/notes").get_json()
    assert (r["page"], r["per_page"], r["total"], r["pages"]) == (1, 10, 25, 3)
    assert len(r["items"]) == 10 and r["has_next"] and not r["has_prev"]
    assert r["items"][0]["title"] == "n24"  # newest first

    r = alice.get("/notes?page=3&per_page=10").get_json()
    assert len(r["items"]) == 5 and not r["has_next"] and r["has_prev"]

    r = alice.get("/notes?page=99").get_json()
    assert r["items"] == [] and r["total"] == 25

    assert alice.get("/notes?per_page=1000").get_json()["per_page"] == 100
    assert alice.get("/notes?page=0").status_code == 400
    assert alice.get("/notes?page=abc").status_code == 400
    assert alice.get("/notes?per_page=-1").status_code == 400


def test_pagination_only_counts_own_notes(alice, bob):
    for i in range(3):
        alice.post("/notes", json={"title": f"a{i}"})
    bob.post("/notes", json={"title": "b"})
    assert alice.get("/notes").get_json()["total"] == 3
    assert bob.get("/notes").get_json()["total"] == 1


def test_json_404_and_405(client):
    assert client.get("/nope").status_code == 404
    assert client.get("/nope").get_json()["errors"]
    assert client.put("/login").status_code == 405
