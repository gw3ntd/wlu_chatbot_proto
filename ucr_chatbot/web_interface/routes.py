from flask import (
    Blueprint,
    render_template,
)
from ucr_chatbot.db.models import Session, engine, Courses, ParticipatesIn
from sqlalchemy import select

bp = Blueprint("web_routes", __name__)

user_email = "test@ucr.edu"


@bp.route("/")
def course_selection():
    """Renders the main landing page with a list of the user's courses."""
    with Session(engine) as session:
        stmt = (
            select(Courses)
            .join(ParticipatesIn, Courses.id == ParticipatesIn.course_id)
            .where(ParticipatesIn.email == user_email)
        )
        courses = session.execute(stmt).scalars().all()

    return render_template(
        "landing_page.html",
        courses=courses,
    )


@bp.route("/new_conversation/<int:course_id>/chat")
def new_conversation(course_id: int):
    """Renders the conversation page for a new conversation.

    :param course_id: The id of the course for which a conversation will be initialized.
    """
    return render_template("conversation.html", course_id=course_id)


@bp.route("/conversation/<int:conversation_id>")
def conversation(conversation_id: int):
    """Renders the conversation page for an existing conversation.

    :param conversation_id: The id of the conversation to be displayed.
    """
    return render_template("conversation.html", conversation_id=conversation_id)


@bp.route("/course/<int:course_id>/documents", methods=["GET", "POST"])
def course_documents(course_id: int):
    """Responds with a page for course document management.

    :param course_id: The id of the course.
    """
    return render_template(
        "base.html",
        title="Course Documents",
        body=f"These are the documents for the course with id {course_id}",
    )
