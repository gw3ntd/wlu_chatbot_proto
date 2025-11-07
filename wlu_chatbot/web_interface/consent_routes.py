from flask import (
    Blueprint,
    request,
    redirect,
)

from flask_login import current_user, login_required  # type: ignore
from typing import Any, Optional


from wlu_chatbot.db.models import Session, get_engine, ConsentForm, Consent
from wlu_chatbot.decorators import roles_required


bp = Blueprint("consent_routes", __name__)


def course_from_concent_form_in_form(_: dict[str, Any]) -> Optional[int]:
    """Gets the course_id from the url of a route"""
    data = request.form
    with Session(get_engine()) as sess:
        consent_form = sess.get(ConsentForm, int(data["consent_form_id"]))
        if consent_form is None:
            return None
        return consent_form.course.id


@bp.post("/consents/")
@login_required
@roles_required(
    ["instructor", "assistant", "student"], course_from_concent_form_in_form
)
def post_consent():
    """Create a new consent"""
    data = request.form

    consent_form_id = int(data["consent_form_id"])

    with Session(get_engine()) as sess:
        consent = Consent(
            consent_form_id=consent_form_id, user_email=current_user.email
        )
        sess.add(consent)
        sess.commit()

    return redirect(request.args.get("next", "/"))
