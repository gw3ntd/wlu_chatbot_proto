from typing import Callable, ParamSpec, Optional, Any
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user  # type: ignore
from ucr_chatbot.db.models import (
    Session as DBSession,
    ParticipatesIn,
    get_engine,
)
from flask.typing import ResponseReturnValue  # type: ignore
# import os

P = ParamSpec("P")  # preserves decorated function's param types


def roles_required(
    allowed_roles: list[str],
    get_course_id: Callable[[dict[str, Any]], Optional[int]],
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
            course_id = get_course_id(kwargs)

            if not course_id:
                flash("Missing course context.", "danger")
                return redirect(url_for("web_interface.general_routes.home"), 400)

            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(
                    url_for("web_interface.authentication_routes.login"), 401
                )

            with DBSession(get_engine()) as db:
                record = (
                    db.query(ParticipatesIn)
                    .filter_by(email=current_user.email, course_id=course_id)
                    .first()
                )

                if not record or record.role not in allowed_roles:
                    flash("You do not have permission to access this page.", "danger")
                    return redirect(url_for("web_interface.general_routes.home"), 403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator
