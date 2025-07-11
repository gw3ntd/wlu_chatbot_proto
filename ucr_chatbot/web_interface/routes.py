from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
    request,
    send_from_directory,
    current_app,
)
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import os
from typing import cast


allowed_extenstions = {"txt", "md", "pdf", "wav", "mp3"}
courses = {
    91: "CS009A",
    92: "CS009B",
    93: "CS009C",
    101: "CS010A",
    102: "CS010B",
    103: "CS010C",
    11: "CS011",
    61: "CS061",
    100: "CS100",
    111: "CS111",
    141: "CS141",
}

bp = Blueprint("routes", __name__)


@bp.route("/")
def course_selection():
    """Responds with a landing page where a student can select a course"""
    body_text = ""
    for course in courses:
        body_text += f'Select your course. <a href="{url_for(".new_conversation", course_id=course)}"> {courses[course]} </a> &emsp; Upload documents for a course: <a href="{url_for(".course_documents", course_id=course)}"> {courses[course]} </a> <br/>'
    return render_template(
        "base.html",
        title="Landing Page",
        body=body_text,
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


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extenstions


@bp.route("/course/<int:course_id>/documents", methods=["GET", "POST"])
def course_documents(course_id: int):
    """Responds with a page where a course administrator can add more documents
    to the course for use by the retrieval-augmented generation system.
    :param course_id: The id of the course for which a conversation will be initialized.
    """
    curr_path: str = cast(str, current_app.config["UPLOAD_FOLDER"])
    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)

        file: FileStorage = request.files["file"]

        if not file.filename:
            return redirect(request.url)

        if file and _allowed_file(file.filename):
            filename: str = secure_filename(file.filename)
            file.save(
                os.path.join(os.path.join(curr_path, courses[course_id]), filename)
            )

    docs_list = os.listdir(os.path.join(curr_path, courses[course_id]))
    doc_string = ""
    for i, doc in enumerate(docs_list):
        print(doc)
        doc_string += f'{i + 1}. <a href="{url_for(".download_file", name=doc)}"> {doc} </a> <br/>'

    return render_template("documents.html", body=doc_string)


@bp.route("/uploads/<name>")
def download_file(name: str):
    """Responds with a page of the specified document that then can be downloaded.
    :param name: The name of the file stored to be downloaded.
    """
    curr_path: str = cast(str, current_app.config["UPLOAD_FOLDER"])
    return send_from_directory(curr_path, name)
