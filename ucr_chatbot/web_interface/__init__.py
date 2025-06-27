"""This module contains the routes for the web interface with which students, instructors, and assistants interact."""

from . import routes
from flask import Blueprint

bp = Blueprint("web_interface", __name__, url_prefix="")
bp.register_blueprint(routes.bp)
