from functools import wraps
from flask import flash, redirect, url_for, request, session  # type: ignore
from flask_login import current_user  # type: ignore
from ucr_chatbot.db.models import Session as DBSession, ParticipatesIn, engine
from typing import Callable, ParamSpec, Optional, cast
from flask.typing import ResponseReturnValue  # type: ignore

P = ParamSpec("P")  # preserves decorated function's param types


def roles_required(
    allowed_roles: list[str],
) -> Callable[[Callable[P, ResponseReturnValue]], Callable[P, ResponseReturnValue]]:
    """
    makes a decorator for gated access
    """

    def decorator(
        f: Callable[P, ResponseReturnValue],
    ) -> Callable[P, ResponseReturnValue]:
        @wraps(f)
        def decorated_function(
            *args: P.args, **kwargs: P.kwargs
        ) -> ResponseReturnValue:
            # Try multiple sources for course_id
            course_id_raw = (
                cast(Optional[str], kwargs.get("course_id"))
                or request.args.get("course_id")
                or request.form.get("course_id")
                or session.get("course_id")
            )

            if not course_id_raw:
                flash("Missing course context.", "danger")
                return redirect(url_for("web_interface.web_routes.home"))

            try:
                course_id = int(str(course_id_raw))
            except (ValueError, TypeError):
                flash("Invalid course ID.", "danger")
                return redirect(url_for("web_interface.web_routes.home"))

            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("web_interface.web_routes.login"))

            with DBSession(engine) as db:
                record = (
                    db.query(ParticipatesIn)
                    .filter_by(email=current_user.email, course_id=int(course_id))
                    .first()
                )

                if not record or record.role not in allowed_roles:
                    flash("You do not have permission to access this page.", "danger")
                    return redirect(url_for("web_interface.web_routes.home"))

            return f(*args, **kwargs)

        return decorated_function

    return decorator
