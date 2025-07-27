from functools import wraps
from flask import flash, redirect, url_for, request, session
from flask_login import current_user
from ucr_chatbot.db.models import Session as DBSession, ParticipatesIn, engine

def roles_required(allowed_roles: list[str]):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Try multiple sources for course_id
            course_id = (
                kwargs.get("course_id")
                or request.args.get("course_id")
                or request.form.get("course_id")
                or session.get("course_id")
            )

            if not course_id:
                flash("Missing course context.", "danger")
                return redirect(url_for("web_interface.web_routes.home"))

            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("web_interface.web_routes.login"))

            with DBSession(engine) as db:
                record = db.query(ParticipatesIn).filter_by(
                    email=current_user.email,
                    course_id=int(course_id)
                ).first()

                if not record or record.role not in allowed_roles:
                    flash("You do not have permission to access this page.", "danger")
                    return redirect(url_for("web_interface.web_routes.home"))

            return f(*args, **kwargs)
        return decorated_function
    return decorator