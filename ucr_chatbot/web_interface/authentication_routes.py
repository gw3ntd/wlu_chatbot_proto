from flask import (
    Blueprint,
    render_template,
    request,
    url_for,
    redirect,
    session,
    flash,
    current_app,
    Response as FlaskResponse,
    make_response,
)

from sqlalchemy import func

from werkzeug.security import check_password_hash
from flask_login import login_required, login_user, logout_user  # type: ignore
from datetime import datetime, timedelta, timezone

from typing import cast, Union, Any, Dict, Mapping


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

    :return: a redirect response to the dashboard or the login page
    :rtype: flask.Response
    """
    # get_flashed_messages()  # clearing flash() messages
    config = cast(Mapping[str, Any], current_app.config)
    max_attempts = cast(int, config.get("MAX_LOGIN_ATTEMPTS", 3))
    cooldown_minutes = 5

    now = datetime.now(timezone.utc)

    last_attempt_time = session.get("last_login_attempt_time")
    if last_attempt_time:
        last_attempt_time = datetime.fromisoformat(last_attempt_time)
        if now - last_attempt_time > timedelta(minutes=cooldown_minutes):
            session["login_attempts"] = 0

    if session.get("login_attempts", 0) >= max_attempts:
        flash("Too many failed login attempts. Please try again later", "error")
        return render_template("index.html")

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        with Session(engine) as db_session:
            user: Users | None = db_session.query(Users).filter_by(email=email).first()

        if user and check_password_hash(cast(str, user.password_hash), password):
            login_user(user)
            session.pop("login_attempts", None)
            session.pop("last_login_attempt_time", None)
            return redirect(
                request.args.get("next")
                or url_for("web_interface.general_routes.course_selection")
            )
        else:
            session["login_attempts"] = session.get("login_attempts", 0) + 1
            session["last_login_attempt_time"] = now.isoformat()
            remaining = max_attempts - session["login_attempts"]
            flash(
                f"Invalid email or password. {remaining} attempt(s) remaining.", "error"
            )
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
    the user. It will either redirect the user to the Google OAuth
    authorization endpoint or, if an error occurs, it returns a 500
    error response.

    :return: a redirect response to Google authorization URL or
    a tuple containing an error message
    :rtype: Response | tuple[str, int]
    """
    try:
        config = cast(Mapping[str, Any], current_app.config)
        max_attempts = cast(int, config.get("MAX_LOGIN_ATTEMPTS", 3))
        cooldown_minutes = 5

        now = datetime.now(timezone.utc)
        last_attempt_time = session.get("last_login_attempt_time")

        if last_attempt_time:
            last_attempt_time = datetime.fromisoformat(last_attempt_time)
            if now - last_attempt_time > timedelta(minutes=cooldown_minutes):
                session["login_attempts"] = 0

        if session.get("login_attempts", 0) >= max_attempts:
            flash("Too many failed login attempts. Please try again later", "error")
            return cast(
                FlaskResponse,
                redirect(url_for("web_interface.authentication_routes.login")),
            )

        google = current_app.oauth.google  # type: ignore
        redirect_uri = url_for(
            "web_interface.authentication_routes.authorize_google", _external=True
        )
        return google.authorize_redirect(redirect_uri)  # type: ignore
    except Exception as e:
        import traceback

        traceback.print_exc()
        return f"<pre>Error occurred during login:<br>{str(e)}</pre>", 500


@bp.route("/authorize/google")
def authorize_google():
    """Google OAuth user verification. If the user is verified,
    they are logged in and redirected to the dashboard endpoint. If they
    can't be verified, an error message pops up.

    :return: redirects user to the dashboard on success or returns an error
    :rtype: Response | tuple[str, int]
    """
    try:
        if "code" not in request.args:
            flash("Google authorization failed: No code received", "error")
            return redirect(url_for("web_interface.authentication_routes.login"))

        google = current_app.oauth.google  # type: ignore
        token = google.authorize_access_token()  # type: ignore
        if not token:
            flash("Google authorization failed: No token received", "error")
            return redirect(url_for("web_interface.authentication_routes.login"))

        userinfo_endpoint = google.server_metadata["userinfo_endpoint"]  # type: ignore
        resp = google.get(userinfo_endpoint)  # type: ignore
        resp.raise_for_status()  # type: ignore
        user_info = cast(Dict[str, Any], resp.json())  # type: ignore

        email: str = user_info["email"]
        with Session(engine) as db_session:
            # user = db_session.query(Users).filter_by(email=email).first()
            user = (
                db_session.query(Users).filter(func.lower(Users.email) == email).first()
            )
            if not user:
                config = cast(Mapping[str, Any], current_app.config)
                session["login_attempts"] = session.get("login_attempts", 0) + 1
                session["last_login_attempt_time"] = datetime.now(
                    timezone.utc
                ).isoformat()
                remaining: int = (
                    cast(int, config.get("MAX_LOGIN_ATTEMPTS", 3))
                    - session["login_attempts"]
                )
                flash(
                    f"Access denied: This email is not authorized. {remaining} attempt(s) remaining.",
                    "error",
                )
                return redirect(url_for("web_interface.authentication_routes.login"))

            login_user(user)  # Log the user in
            session.pop("login_attempts", None)
            session.pop("last_login_attempt_time", None)
            # session.regenerate()
        return redirect(url_for("web_interface.general_routes.course_selection"))
    except Exception as e:
        import traceback

        traceback.print_exc()
        flash(f"Authorization error: {str(e)}", "error")
        return f"<pre>Authorization error:<br>{str(e)}</pre>", 500
