"""Flask application factory and route registration."""
from flask import Flask
from flask_restful import Api

from config import Config
from extensions import bcrypt, db, migrate
from resources.auth import CheckSession, Login, Logout, Signup
from resources.notes import NoteDetail, NoteList


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.json.sort_keys = False

    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    api = Api(app)
    api.add_resource(Signup, "/signup")
    api.add_resource(Login, "/login")
    api.add_resource(CheckSession, "/check_session")
    api.add_resource(Logout, "/logout")
    api.add_resource(NoteList, "/notes")
    api.add_resource(NoteDetail, "/notes/<int:note_id>")

    register_error_handlers(app)
    return app


def register_error_handlers(app):
    """Return JSON for errors raised outside Flask-RESTful resources."""

    @app.errorhandler(404)
    def not_found(_e):
        return {"errors": ["Resource not found."]}, 404

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return {"errors": ["Method not allowed."]}, 405

    @app.errorhandler(500)
    def server_error(_e):
        return {"errors": ["Internal server error."]}, 500


app = create_app()

if __name__ == "__main__":
    app.run(port=5555, debug=True)
