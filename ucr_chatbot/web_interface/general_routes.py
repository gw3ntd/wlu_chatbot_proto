from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
)

from sqlalchemy import select


from flask_login import current_user, login_required  # type: ignore


from ucr_chatbot.db.models import (
    Session,
    engine,
    Courses,
    ParticipatesIn,
)


bp = Blueprint("general_routes", __name__)


@bp.route("/")
def home():
    """Login page for the user. If the user is already
    logged in, they are redirected to the dashboard

    :return: a redirect response to the dashboard or the login page
    :rtype: flask.Response
    """
    if current_user.is_authenticated:
        return redirect(url_for("web_interface.general_routes.course_selection"))
    return render_template("index.html")


@bp.route("/course_selection")
@login_required
def course_selection():
    """Renders the main landing page with a list of the user's courses."""
    user_email = current_user.email
    with Session(engine) as session:
        stmt = (
            select(Courses, ParticipatesIn.role)
            .join(ParticipatesIn, Courses.id == ParticipatesIn.course_id)
            .where(ParticipatesIn.email == user_email)
        )

        courses = session.execute(stmt).all()

    return render_template(
        "landing_page.html",
        courses=courses,
        email=current_user.email,
    )
