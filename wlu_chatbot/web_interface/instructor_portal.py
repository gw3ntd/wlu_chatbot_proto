from typing import Optional, cast, Any

from flask import (
    Blueprint,
    render_template,
    request,
    abort,
    Response as FlaskResponse,
)

from sqlalchemy import select
from flask_login import login_required  # type: ignore
from datetime import datetime

from wlu_chatbot.decorators import roles_required
from wlu_chatbot.db.models import (
    Session,
    get_engine,
    Course,
    ParticipatesIn,
    Document,
    User,
)

from wlu_chatbot.api.summary_generation import generate_usage_summary

bp = Blueprint("instructor_portal", __name__)


def course_from_document_in_url(kwargs: dict[str, Any]) -> Optional[int]:
    """Gets the course_id from the file_path in the url."""
    with Session(get_engine()) as sess:
        doc = sess.get(Document, kwargs["file_path"])
        if not doc:
            return None
        return cast(int, doc.course_id)


def course_from_url(kwargs: dict[str, Any]) -> int:
    """Gets the course_id from the url of a route"""
    return int(kwargs["course_id"])


@bp.route("/courses/<int:course_id>/instructor-portal", methods=["GET"])
@login_required
@roles_required(["instructor"], course_from_url)
def instructor_portal(course_id: int):
    """Course management page for instructors."""

    with Session(get_engine()) as sess:
        course = sess.get(Course, course_id)
        if course is None:
            abort(404)

        documents = sess.query(Document).where(Document.course_id == course_id).all()
        students = (
            sess.query(User)
            .join(ParticipatesIn)
            .where(
                ParticipatesIn.course_id == course_id, ParticipatesIn.role == "student"
            )
            .all()
        )
        assistants = (
            sess.query(User)
            .join(ParticipatesIn)
            .where(
                ParticipatesIn.course_id == course_id,
                ParticipatesIn.role == "assistant",
            )
            .all()
        )
        return render_template(
            "instructor_portal.html",
            course=course,
            documents=documents,
            students=students,
            assistants=assistants,
        )


def conv_date(date: Optional[str]) -> Optional[datetime]:
    """Converts datetime input into proper formatting"""
    if not date or date == "":
        return None
    return datetime.fromisoformat(date)


@bp.route("/courses/<int:course_id>/summaries", methods=["POST"])
@login_required
@roles_required(["instructor"], course_from_url)
def post_summary(course_id: int):
    """Generates a summary of student conversations for a course
    :param course_id: The course that is to be summarised.
    """
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")

    if end_date and not start_date:
        end_date = None

    start_date = conv_date(start_date)
    end_date = conv_date(end_date)

    with Session(get_engine()) as session:
        stmt = select(Course.name).where(Course.id == course_id)

        course_name = session.execute(stmt).scalar_one()

    summary = generate_usage_summary(course_id, start_date, end_date, course_name)

    return FlaskResponse(
        summary,
        mimetype="text/plain",
        headers={
            "Content-disposition": f"attachment; filename={course_name}_Report.txt"
        },
    )
