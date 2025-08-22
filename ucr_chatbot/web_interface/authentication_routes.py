from flask import (
    Blueprint,
    render_template,
    request,
    url_for,
    redirect,
    flash,
    current_app,
    Response as FlaskResponse,
    make_response,
    abort,
)

from sqlalchemy import func

from werkzeug.security import check_password_hash
from flask_login import login_required, login_user, logout_user  # type: ignore

from typing import cast, Union, Any, Dict


from ucr_chatbot.db.models import (
    Session,
    engine,
    Users,
)

bp = Blueprint("authentication_routes", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Checks if the user has valid login credentials. If they do, the
    user is successfully logged in and redirected to the dashboard
    """

    if current_app.config["REQUIRE_OAUTH"]:
        abort(403, description="OAuth login is required.")

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        with Session(engine) as db_session:
            user: Users | None = db_session.query(Users).filter_by(email=email).first()

        if user and check_password_hash(cast(str, user.password_hash), password):
            login_user(user)
            return redirect(
                request.args.get("next")
                or url_for("web_interface.general_routes.course_selection")
            )
        else:
            flash("Invalid email or password.", "error")
    rendered_template = render_template("index.html")
    response = make_response(rendered_template)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@bp.route("/logout")
@login_required
def logout():
    """The user is sucessfully logged out and redirected to
    the home page

    :return: a redirect response to the home page
    :rtype: flask.Response
    """
    logout_user()
    return redirect(url_for("web_interface.general_routes.home"))


@bp.route("/login/google")
def login_google() -> Union[FlaskResponse, tuple[str, int]]:
    """This function starts the Google OAuth login process for
    the user. It will redirect the user to the Google OAuth
    authorization endpoint.
    """

    google = current_app.config["OAUTH"].google  # type: ignore
    redirect_uri = url_for(
        "web_interface.authentication_routes.authorize_google", _external=True
    )
    return google.authorize_redirect(redirect_uri)  # type: ignore


@bp.route("/authorize/google")
def authorize_google():
    """Google OAuth user verification. If the user is verified,
    they are logged in and redirected to the dashboard endpoint. If they
    can't be verified, an error message pops up.
    """

    if "code" not in request.args:
        flash("Google authorization failed: No code received", "error")
        return redirect(url_for("web_interface.general_routes.home"))

    google = current_app.config["OAUTH"].google  # type: ignore
    token = google.authorize_access_token()  # type: ignore
    if not token:
        flash("Could not verify account with Google.", "error")
        return redirect(url_for("web_interface.general_routes.home"))

    userinfo_endpoint = google.server_metadata["userinfo_endpoint"]  # type: ignore
    resp = google.get(userinfo_endpoint)  # type: ignore
    resp.raise_for_status()  # type: ignore
    user_info = cast(Dict[str, Any], resp.json())  # type: ignore

    email: str = user_info["email"]
    with Session(engine) as db_session:
        user = db_session.query(Users).filter(func.lower(Users.email) == email).first()
        if not user:
            flash(
                "Access denied: This account is not authorized to use this application.",
                "error",
            )
            return redirect(url_for("web_interface.general_routes.home"))

        login_user(user)

    return redirect(url_for("web_interface.general_routes.course_selection"))
