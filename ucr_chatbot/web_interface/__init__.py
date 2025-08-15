"""This module contains the routes for the web interface with which students, instructors, and assistants interact."""

from . import authentication_routes
from . import instructor_routes
from . import assistant_routes
from . import conversation_routes
from . import general_routes
from flask import Blueprint

bp = Blueprint("web_interface", __name__, url_prefix="")
bp.register_blueprint(authentication_routes.bp, url_prefix="")
bp.register_blueprint(instructor_routes.bp, url_prefix="")
bp.register_blueprint(assistant_routes.bp, url_prefix="")
bp.register_blueprint(conversation_routes.bp, url_prefix="")
bp.register_blueprint(general_routes.bp, url_prefix="")
