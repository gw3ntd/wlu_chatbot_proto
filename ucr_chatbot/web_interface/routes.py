from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
)

bp = Blueprint("routes", __name__)


@bp.route("/")
def course_selection():
    """Responds with a landing page where a student can select a course"""
    return render_template(
        "base.html",
        title="Landing Page",
        body=f'Select your course. <a href="{url_for(".new_conversation", course_id="1")}"> CS009A </a>',
    )


@bp.route("/course/<int:course_id>/chat")
def new_conversation(course_id: int):
    """Redirects to a page with a new conversation for a course.
    :param course_id: The id of the course for which a conversation will be initialized.
    """
    return redirect(url_for(".conversation", conversation_id=course_id))


@bp.route("/convsersation/<int:conversation_id>")
def conversation(conversation_id: int):
    """Responds with page where a student can interact with a chatbot for a course.

    :param conversation_id: The id of the conversation to be send back to the user.
    """
    return render_template(
        "base.html",
        title="Landing Page",
        body=f"Chat with me about the course for which the conversation with id {conversation_id} exists.",
    )


@bp.route("/course/<int:course_id>/documents")
def course_documents(course_id: int):
    """Responds with a page where a course administrator can add more documents
    to the course for use by the retrieval-augmented generation system.
    :param course_id: The id of the course for which a conversation will be initialized.
    """
    return render_template(
        "base.html",
        title="Landing Page",
        body=f"These are the documents for the course with id {course_id}",
    )
