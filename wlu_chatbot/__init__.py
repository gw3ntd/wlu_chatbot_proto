"""Contains a Flask application for a tutoring chatbot,
including a public web interface and an API for interacting with the chatbot.
"""

from typing import Mapping, Any
from pathlib import Path

from flask import Flask, current_app
from flask_login import LoginManager  # type: ignore
from authlib.integrations.flask_client import OAuth  # type: ignore

from wlu_chatbot.db.models import User, Session, get_engine
from wlu_chatbot.config import Config, app_config

import os

import os

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")



def create_app(test_config: Mapping[str, Any] | None = None):
    """Creates a Flask application for the WLU Chatbot.

    :param test_config: If specified, sets the config for the returned Flask application, defaults to None
    :return: The Flask application.
    """

    app = Flask(__name__, instance_relative_config=True)
    app.debug = True
    app.config["PROPAGATE_EXCEPTIONS"] = True

    app.config.from_object(Config)
    if test_config:
        app.config.from_mapping(test_config)

    instance_path = Path(app.instance_path)
    if not instance_path.is_dir():
        instance_path.mkdir(parents=True, exist_ok=True)

    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True

    login_manager = LoginManager()
    login_manager.init_app(app)  # type: ignore
    login_manager.login_view = "web_interface.authentication_routes.login"  # type: ignore

    @login_manager.user_loader  # type: ignore
    def load_user(user_email: int):  # pyright: ignore[reportUnusedFunction]
        with Session(get_engine()) as session:
            return session.get(User, user_email)

    with app.app_context():
        oauth = OAuth(current_app)
        oauth.init_app(current_app)  # type: ignore

        oauth.register(  # type: ignore
            name="google",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid profile email"},
        )

        app.config["OAUTH_CLIENT"] = oauth

    from wlu_chatbot import web_interface

    app.register_blueprint(web_interface.bp)

    return app