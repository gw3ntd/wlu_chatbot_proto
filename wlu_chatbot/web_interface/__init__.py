"""This module contains the routes for the web interface with which students, instructors, and assistants interact."""

from . import authentication_routes
from . import instructor_portal
from . import assistant_routes
from . import conversation_routes
from . import general_routes
from . import consent_form_routes
from . import consent_routes
from . import message_routes
from . import limit_routes
from . import document_routes
from . import participates_in_routes
from flask import Blueprint

bp = Blueprint("web_interface", __name__, url_prefix="")
bp.register_blueprint(authentication_routes.bp, url_prefix="")
bp.register_blueprint(instructor_portal.bp, url_prefix="")
bp.register_blueprint(assistant_routes.bp, url_prefix="")
bp.register_blueprint(conversation_routes.bp, url_prefix="")
bp.register_blueprint(general_routes.bp, url_prefix="")
bp.register_blueprint(consent_form_routes.bp, url_prefix="")
bp.register_blueprint(consent_routes.bp, url_prefix="")
bp.register_blueprint(message_routes.bp, url_prefix="")
bp.register_blueprint(limit_routes.bp, url_prefix="")
bp.register_blueprint(document_routes.bp, url_prefix="")
bp.register_blueprint(participates_in_routes.bp, url_prefix="")
