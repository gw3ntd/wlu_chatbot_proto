from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    redirect,
    abort,
)

from flask_login import login_required  # type: ignore
from typing import Any, Optional


from wlu_chatbot.db.models import (
    Session,
    get_engine,
    ConsentForm,
)
from wlu_chatbot.decorators import roles_required


bp = Blueprint("consent_form_routes", __name__)


def course_from_consent_form_in_url(kwargs: dict[str, Any]) -> Optional[int]:
    """Get the course_id from the consent_form_id in the url"""
    with Session(get_engine()) as sess:
        consent_form = sess.get(ConsentForm, kwargs["consent_form_id"])
        if consent_form is None:
            return None
        return consent_form.course.id


def course_from_form(_: dict[str, Any]) -> Optional[int]:
    """Gets the course_id from the url of a route"""
    data = request.form
    return int(data["course_id"])


@bp.get("/consent-forms/<int:consent_form_id>")
@login_required
@roles_required(["instructor", "assistant", "student"], course_from_consent_form_in_url)
def get_consent_form(consent_form_id: int):
    """Displays a consent form."""
    with Session(get_engine()) as sess:
        consent_form = sess.get(ConsentForm, consent_form_id)
        if consent_form is None:
            abort(404)
    return render_template("consent_form.html", consent_form=consent_form)


@bp.post("/consent-forms/")
@login_required
@roles_required(["instructor"], course_from_form)
def post_consent_form():
    """Creates a consent form."""
    data = request.form

    course_id = int(data["course_id"])
    body = str(data["body"])
    title = str(data["title"])

    with Session(get_engine()) as sess:
        consent_form = ConsentForm(course_id=course_id, body=body, title=title)
        sess.add(consent_form)
        sess.commit()

    if request.referrer:
        return redirect(request.referrer)
    else:
        return redirect("/")


@bp.delete("/consent-forms/<int:consent_form_id>")
@login_required
@roles_required(["instructor"], course_from_consent_form_in_url)
def delete_consent_form(consent_form_id: int):
    """Deletes a consent form."""
    with Session(get_engine()) as sess:
        consent_form = sess.get(ConsentForm, consent_form_id)
        if consent_form is None:
            abort(404)
        sess.delete(consent_form)
        sess.commit()

    if request.referrer:
        redirect_url = request.referrer
    else:
        redirect_url = "/"

    return jsonify({"success": True, "redirect_url": redirect_url})
