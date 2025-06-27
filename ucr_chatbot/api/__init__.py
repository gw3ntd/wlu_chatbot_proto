"""This module contains the routes for the API endpoints."""

from . import routes
from flask import Blueprint

bp = Blueprint("api", __name__, url_prefix="/api")
bp.register_blueprint(routes.bp)
