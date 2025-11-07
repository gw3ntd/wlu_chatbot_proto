from typing import Optional, Any

from flask import (
    Blueprint,
    request,
    abort,
    flash,
    redirect,
)


from flask_login import login_required  # type: ignore
from pydantic import BaseModel as PydanticModel

from wlu_chatbot.decorators import roles_required


from wlu_chatbot.db.models import (
    Session,
    get_engine,
    ParticipatesIn,
    User,
)
import random

bp = Blueprint("participates_in_routes", __name__)


def course_from_form(_: dict[str, Any]) -> Optional[int]:
    """"""
    course_id = request.form.get("course_id")
    if course_id is None:
        return None
    return int(course_id)


def course_from_form_or_json_body(_: dict[str, Any]) -> Optional[int]:
    """"""
    course_id = request.form.get("course_id")
    if course_id is None and request.json:
        course_id = request.json.get("course_id")
    if course_id is None:
        return None
    return int(course_id)


def course_from_url(kwargs: dict[str, Any]) -> int:
    """Gets the course_id from the url of a route"""
    return int(kwargs["course_id"])


@bp.route("/participates_ins", methods=["POST"])
@login_required
@roles_required(["instructor"], course_from_form_or_json_body)
def post_participates_in():
    """Adds a student to the current course."""

    if request.form:
        data = PostParticipatesInRequest.model_validate(request.form.to_dict())
    elif request.json:
        data = PostParticipatesInRequest.model_validate(request.json)
    else:
        abort(400, "No data provided.")

    if isinstance(data.email, str):
        data.email = [data.email]

    added_emails: set[str] = set()
    with Session(get_engine()) as sess:
        for email in data.email:
            participation = (
                sess.query(ParticipatesIn)
                .where(
                    ParticipatesIn.course_id == data.course_id,
                    ParticipatesIn.email == email,
                )
                .first()
            )
            if participation:
                continue

            if not sess.get(User, email):
                user = User(email=email)
                user.set_password(random.randbytes(16).hex())
                sess.add(user)

            participation = ParticipatesIn(
                email=email,
                course_id=data.course_id,
                role=data.role,
            )
            sess.add(participation)
            added_emails.add(email)
        sess.commit()

    if len(added_emails) == 0 and len(data.email) == 1:
        flash(f"{data.email[0]} has already been added in this course.", "error")
    elif len(data.email) == 0:
        flash("No participants found in CSV.", "error")
    elif len(added_emails) == 0:
        flash(
            "No participants were addeded because all participants in the CSV were already added.",
            "error",
        )
    elif len(added_emails) > 10:
        flash(f"Added {len(data.email)} participant(s) as {data.role}(s).", "info")
    else:
        for email in added_emails:
            flash(f"Added '{email}' as a(n) {data.role}", "info")

    return redirect(request.referrer or "/")


@bp.route("/participates_in/<int:course_id>/<email>", methods=["DELETE"])
@login_required
@roles_required(["instructor"], course_from_url)
def delete_participates_in(course_id: int, email: str):
    """Removes a student or assistant from the current course."""

    with Session(get_engine()) as session:
        p_in = (
            session.query(ParticipatesIn)
            .filter(
                ParticipatesIn.email == email,
                ParticipatesIn.course_id == course_id,
            )
            .first()
        )
        if not p_in:
            flash(
                f"There is no course participant with the email '{email}' in this course.",
                "error",
            )
            return "", 404
        if p_in.role == "instructor":  # type: ignore
            abort(403, "Cannot remove an instructor from a course.")

        session.delete(p_in)
        session.commit()
        flash(f"Removed '{p_in.email}' as a(n) {p_in.role}", "info")

    return "", 204


class PostParticipatesInRequest(PydanticModel):
    email: str | list[str]
    role: str
    course_id: int
