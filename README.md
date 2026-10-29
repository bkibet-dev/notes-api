# Notes API

A secure Flask REST API for a personal notes app. Users sign up, log in with
cookie-based sessions, and manage their own notes. Nobody can see or change
anyone else's notes.

Built for the "Full Auth Flask Backend" summative lab. It matches the
**sessions** React client (`client-with-sessions`) from the lab repo.

## Features

- Session authentication (signup, login, check session, logout)
- Passwords hashed with Flask-Bcrypt; the hash is never returned by the API
- `Note` resource owned by a user, with full CRUD
- Pagination on the notes index
- Every notes route requires login and is scoped to the logged-in user
- Consistent JSON errors: `{"errors": ["..."]}`
- Database migrations (Flask-Migrate), seed script (Faker), pytest suite

## Project structure

```
Pipfile
server/
  app.py            # app factory, route registration, JSON error handlers
  config.py         # configuration (env-overridable)
  extensions.py     # db, bcrypt, migrate instances
  models.py         # User, Note
  schemas.py        # marshmallow validation / serialization
  auth.py           # login_required decorator, error helper
  resources/
    auth.py         # /signup /login /check_session /logout
    notes.py        # /notes and /notes/<id>
  seed.py           # example data
  migrations/       # Alembic migrations
  tests/            # pytest suite
```

## Installation

Requires Python 3.8+ and [Pipenv](https://pipenv.pypa.io/).

```bash
pipenv install
pipenv shell
cd server
export FLASK_APP=app.py
flask db upgrade      # create the tables from the included migration
python seed.py        # load example data (WARNING: wipes existing users/notes)
```

Optional: `export SECRET_KEY="a-long-random-string"` (the session cookie is
signed with it; the built-in default is for development only).

The seed creates three users, all with the password `password123`:
`alice` (25 notes, enough to try pagination), `bob` (8) and `carol` (3).

## Run

```bash
cd server
flask run -p 5555     # or: python app.py
```

The API listens on `http://localhost:5555`, the port the sessions client's
`proxy` setting expects. To use the frontend:

```bash
cd client-with-sessions
npm install
npm start             # http://localhost:4000
```

## Tests

```bash
cd server
python -m pytest
```

## API reference

All request and response bodies are JSON. Errors look like
`{"errors": ["message", ...]}`.

### Auth

| Method | Endpoint | Description | Success | Errors |
|---|---|---|---|---|
| POST | `/signup` | Create an account and log in. Body: `username` (3-30 chars, unique), `password` (min 8), `password_confirmation`. | `201` `{id, username}` | `422` validation, `409` username taken |
| POST | `/login` | Log in. Body: `username`, `password`. Sets the session cookie. | `200` `{id, username}` | `401` invalid credentials |
| GET | `/check_session` | Return the logged-in user (used on page load). | `200` `{id, username}` | `401` `{}` when logged out |
| DELETE | `/logout` | End the session. | `204` no body | none (always succeeds) |

### Notes (login required)

A note has: `id`, `title` (required, 1-100 chars), `content` (text, defaults
to empty), `created_at`, `updated_at`, `user_id` (set by the server, read-only).

Any request without a valid session gets `401`. Requesting a note that does
not exist **or belongs to someone else** returns `404`, so the API never
reveals which note ids exist for other users.

| Method | Endpoint | Description | Success | Errors |
|---|---|---|---|---|
| GET | `/notes?page=1&per_page=10` | Paginated list of **your** notes, newest first. | `200` | `400` bad `page`/`per_page` |
| POST | `/notes` | Create a note. Body: `title`, optional `content`. | `201` the note | `400` body not a JSON object, `422` validation |
| GET | `/notes/<id>` | Get one of your notes. | `200` the note | `404` |
| PATCH | `/notes/<id>` | Update `title` and/or `content`. | `200` the note | `400` empty body, `404`, `422` validation |
| DELETE | `/notes/<id>` | Delete one of your notes. | `204` no body | `404` |

**Pagination.** `page` defaults to 1 and `per_page` to 10 (maximum 100; larger
values are capped). The index response is:

```json
{
  "items": [ { "id": 5, "title": "...", "content": "...", "created_at": "...", "updated_at": "...", "user_id": 1 } ],
  "page": 1, "per_page": 10, "total": 25, "pages": 3,
  "has_next": true, "has_prev": false
}
```

A page past the end returns an empty `items` list.

## Try it with curl

```bash
curl -c jar -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"password123"}' localhost:5555/login

curl -b jar 'localhost:5555/notes?page=1&per_page=5'

curl -b jar -H 'Content-Type: application/json' \
  -d '{"title":"Hello","content":"First note"}' localhost:5555/notes
```
