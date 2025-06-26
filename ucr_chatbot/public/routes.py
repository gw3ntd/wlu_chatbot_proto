from flask import Blueprint, render_template

bp = Blueprint('root', __name__, '/')

@bp.route("/")
def course_selection():
    return render_template("base.html", title="Landing Page", body="Select your course.")

@bp.route("/chat")
def chat():
    return render_template("base.html", title="Landing Page", body="Chat with me!")