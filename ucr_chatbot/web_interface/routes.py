from flask import Blueprint, render_template, url_for

bp = Blueprint("routes", __name__)


@bp.route("/")
def course_selection():
    """Responds with a landing page where a student can select a course"""
    return render_template(
        "base.html",
        title="Landing Page",
        body=f'Select your course. <a href="{url_for(".chat", course_id="1")}"> CS009A </a>',
    )


@bp.route("/chat/<int:course_id>")
def chat(course_id: int):
    """Responds with page where a student can interact with a chatbot for a course with <course_id>."""
    return render_template(
        "base.html",
        title="Landing Page",
        body=f"Chat with me about the course with id {course_id}!",
    )
