from typing import Callable, ParamSpec, Optional, Any
from functools import wraps

from flask import flash, redirect, url_for, request, g, abort
from flask.typing import ResponseReturnValue  # type: ignore

from flask_login import current_user  # type: ignore

from sqlalchemy.orm import Session
from wlu_chatbot.db.models import (
    ParticipatesIn,
    ConsentForm,
    Consent,
    get_engine,
)
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
                abort(400, "Missing course_id")

            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(
                    url_for("web_interface.authentication_routes.login"), 401
                )

            with Session(get_engine()) as session:
                record = (
                    session.query(ParticipatesIn)
                    .filter_by(email=current_user.email, course_id=course_id)
                    .first()
                )

                if not record or record.role not in allowed_roles:
                    flash("You do not have permission to access this page.", "danger")
                    return redirect(url_for("web_interface.general_routes.home"), 403)

                g.role = record.role

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def consent_required(
    get_course_id: Callable[[dict[str, Any]], Optional[int]],
) -> Callable[[Callable[P, ResponseReturnValue]], Callable[P, ResponseReturnValue]]:
    """
    makes a decorator for gating access only to users that hve consented to all forms set for a course.
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

            with Session(get_engine()) as session:
                participation = (
                    session.query(ParticipatesIn)
                    .filter_by(email=current_user.email, course_id=course_id)
                    .first()
                )

                if not participation:
                    flash("You do not have permission to access this page.", "danger")
                    return redirect(url_for("web_interface.general_routes.home"), 403)

                # Get the next consent form for this course to which the current user has not consented
                consent_form = (
                    session.query(ConsentForm)
                    .where(ConsentForm.course_id == course_id)
                    .join(
                        Consent,
                        (ConsentForm.id == Consent.consent_form_id)
                        & (Consent.user_email == current_user.email),
                        isouter=True,
                    )
                    .filter(Consent.consent_form_id.is_(None))
                    .order_by(ConsentForm.id)
                    .first()
                )

            if consent_form is None:
                return f(*args, **kwargs)

            return redirect(
                url_for(
                    "web_interface.consent_form_routes.get_consent_form",
                    consent_form_id=consent_form.id,
                    next=request.full_path,
                )
            )

        return decorated_function

    return decorator
