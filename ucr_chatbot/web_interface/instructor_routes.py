from flask import (
    Blueprint,
    render_template,
    request,
    url_for,
    redirect,
    send_from_directory,
    abort,
    flash,
    Response as FlaskResponse,
)

from sqlalchemy import select
from pathlib import Path
import pandas as pd
import io
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_login import current_user, login_required  # type: ignore
from datetime import datetime
from ucr_chatbot.decorators import roles_required
from typing import Optional


from ucr_chatbot.db.models import (
    Session,
    engine,
    Courses,
    ParticipatesIn,
    Documents,
    add_new_document,
    store_segment,
    store_embedding,
    get_active_documents,
    set_document_inactive,
    add_user_to_course,
    add_students_from_list,
    add_assistants_from_list,
    Users,
)
from ucr_chatbot.config import Config

from ucr_chatbot.api.summary_generation import generate_usage_summary


from ucr_chatbot.api.file_parsing.file_parsing import parse_file
from ucr_chatbot.api.embedding.embedding import embed_text

bp = Blueprint("instructor_routes", __name__)


@bp.route("/course/<int:course_id>/documents", methods=["GET", "POST"])
@login_required
@roles_required(["instructor"])
def course_documents(course_id: int):
    """Page where user uploads and sees their documents for a specific course.

    Supports GET requests to display the documents the user uploads and
    POST requests to upload a new document.

    The uploaded files are saved to a user- and course-specific directory on the server.
    Only allowed file types can be uploaded.

    Uploaded documents are listed with options to download or delete each file.

    :param course_id: unique identifier for course where documents are uploaded
    :type course_id: int

    :raises 404: If the current user is not found in the database.

    :return: the document upload form, any error messages, and a list of the user's uploaded documents for the course.
    :rtype: flask.Response

    """
    email = current_user.email
    with Session(engine) as session:
        user = session.query(Users).filter_by(email=email).first()
    if user is None:
        abort(404, description="User not found")
    curr_path = Config.FILE_STORAGE_PATH
    error_msg = ""

    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part", "error")
            return redirect(request.url)

        file: FileStorage = request.files["file"]
        if not file.filename:
            flash("No selected file", "error")
            return redirect(request.url)

        full_local_path = None
        try:
            filename = secure_filename(file.filename)
            relative_path = Path(str(course_id)) / filename
            full_local_path = curr_path / relative_path

            create_upload_folder(course_id=course_id)
            file.save(str(full_local_path))

            segments = parse_file(str(full_local_path))
            add_new_document(
                str(relative_path).replace(str(Path().anchor), ""),
                course_id,
            )
            for seg in segments:
                seg_id = store_segment(
                    seg,
                    str(relative_path).replace(str(Path().anchor), ""),
                )

                embedding = embed_text(seg)
                store_embedding(embedding, seg_id)
            flash("File uploaded and processed successfully!", "success")
            return redirect(url_for(".course_documents", course_id=course_id))

        except (ValueError, TypeError):
            if full_local_path and full_local_path.exists():
                full_local_path.unlink()
            flash("You can't upload this type of file", "error")

    docs_html = ""
    active_docs = get_active_documents()
    docs_dir = Path(curr_path) / str(course_id)
    if docs_dir.is_dir():
        for idx, doc in enumerate(docs_dir.iterdir(), 1):
            if not doc.is_file():
                continue

            file_path = str(Path(str(course_id)) / secure_filename(doc.name))
            # file_path = f"{course_id}/{secure_filename(doc.name)}"

            if file_path not in active_docs:
                continue

            docs_html += f"""
              <div style="margin-bottom:4px;">
                  {idx}. <a href="{url_for(".download_file", file_path=file_path)}">{doc.name}</a>
                  <form action="{url_for(".delete_document", file_path=file_path)}" method="post" style="display:inline;">
                      <button type="submit" onclick="return confirm('Delete {doc.name}?');">Delete</button>

                  </form>
              </div>
            """

    body = error_msg + (docs_html or "No documents uploaded yet.")
    return render_template("documents.html", body=body, course_id=course_id)


@bp.route("/document/<path:file_path>/delete", methods=["POST"])
@login_required
@roles_required(["instructor"])
def delete_document(file_path: str):
    """Deletes a document uploaded by a user in a specific course

    Verifies that the current user matches the username parameter.

    If the user or document does not exist, it raises a 404 error.

    :param course_id: course ID of where the document is
    :type course_id: int
    :param username: username of document's owner
    :type username: str
    :param filename: filename of the document to delete
    :type filename: str

    :raises 403: the logged-in user does not match the provided username
    :raises 404: the user or document does not exist in the database

    :return: Redirects to the document listing page for the course after it is deleted
    :rtype: flask.Response
    """
    email = current_user.email

    if current_user.is_anonymous:
        abort(403)

    full_path = str(Path(Config.FILE_STORAGE_PATH) / file_path)

    with Session(engine) as session:
        document = session.query(Documents).filter_by(file_path=file_path).first()
        if document is None:
            abort(404, description="Document not found")

        participation = (
            session.query(ParticipatesIn)
            .filter_by(email=email, course_id=document.course_id)
            .first()
        )
        if not participation:
            abort(
                403, description="You do not have permission to delete this document."
            )

        course_id = document.course_id

        if Path(full_path).exists():
            set_document_inactive(file_path)

    return redirect(url_for(".course_documents", course_id=course_id))


@bp.route("/document/<path:file_path>/download", methods=["GET"])
@login_required
@roles_required(["instructor"])
def download_file(file_path: str):
    """this function delivers a file that was already uploaded by a user
    and it makes sure that only the authorized user can download the file

    :param course_id: the ID of the course the file belongs to
    :type course_id: int
    :param username: the username of the user who owns the file
    :type username: str
    :param name: the name of the file to be downloaded
    :type name: str

    :raises 403: if the current user does not match the username parameter

    :return: a response object to send the requested file from the user's upload directory
    :rtype: flask.wrappers.Response
    """
    email = current_user.email
    with Session(engine) as session:
        document = session.query(Documents).filter_by(file_path=file_path).first()
        if document is None:
            abort(404)

        participation = (
            session.query(ParticipatesIn)
            .filter_by(email=email, course_id=document.course_id)
            .first()
        )
        if not participation:
            abort(403)

    path_obj = Path(file_path)
    directory = str(path_obj.parent)
    name = path_obj.name
    return send_from_directory(str(Path(Config.FILE_STORAGE_PATH) / directory), name)


@bp.route("/course/<int:course_id>/add_student", methods=["POST"])
@login_required
@roles_required(["instructor"])
def add_student(course_id: int):
    """Adds a student to the current course.
    :param course_id: The course the student will be added to.
    """
    user_email = request.form["email"]
    user_fname = request.form["fname"]
    user_lname = request.form["lname"]
    role = request.form.get("role", "student")  # Default to student if not provided

    add_user_to_course(user_email, user_fname, user_lname, course_id, role)
    return redirect(url_for(".course_documents", course_id=course_id))


def conv_date(date: Optional[str]) -> Optional[datetime]:
    """Converts datetime input into proper formatting"""
    if not date or date == "":
        return None
    return datetime.fromisoformat(date)


@bp.route("/course/<int:course_id>/generate_summary", methods=["POST"])
@login_required
@roles_required(["instructor"])
def generate_summary(course_id: int):
    """Generates a summary of student conversations for a course
    :param course_id: The course that is to be summarised.
    """
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")

    if end_date and not start_date:
        end_date = None

    start_date = conv_date(start_date)
    end_date = conv_date(end_date)

    with Session(engine) as session:
        stmt = select(Courses.name).where(Courses.id == course_id)

        course_name = session.execute(stmt).scalar_one()

    summary = generate_usage_summary(course_id, start_date, end_date, course_name)

    return FlaskResponse(
        summary,
        mimetype="text/plain",
        headers={
            "Content-disposition": f"attachment; filename={course_name}_Report.txt"
        },
    )


@bp.route("/course/<int:course_id>/add_from_csv", methods=["POST"])
@login_required
@roles_required(["instructor"])
def add_from_csv(course_id: int):
    """Adds multiple students an uploaded student list csv file.
    :params course_id: The course the students will be added to.
    """
    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)

        file: FileStorage = request.files["file"]
        if not file or not file.filename or not file.filename.endswith(".csv"):
            return redirect(request.url)
        try:
            if file and file.filename.endswith(".csv"):
                stream = io.TextIOWrapper(file.stream, encoding="utf-8")
                data: pd.DataFrame = pd.read_csv(  # type: ignore
                    stream,
                    header=0,
                    skiprows=[1, 2],
                    usecols=["Student", "SIS User ID"],
                    dtype=str,  # type: ignore
                )
                data["Student"] = data["Student"].str.strip()
                data[["Last Name", "First Name"]] = data["Student"].str.split(",")
                add_students_from_list(data, course_id)
        except Exception:
            return redirect(request.url)

    return redirect(url_for(".course_documents", course_id=course_id))


@bp.route("/course/<int:course_id>/add_assistant", methods=["POST"])
@login_required
@roles_required(["instructor"])
def add_assistant(course_id: int):
    """Adds an assistant to the current course.
    :param course_id: The course the assistant will be added to.
    """
    user_email = request.form["email"]
    user_fname = request.form["fname"]
    user_lname = request.form["lname"]
    role = request.form.get("role", "assistant")

    add_user_to_course(user_email, user_fname, user_lname, course_id, role)
    return redirect(url_for(".course_documents", course_id=course_id))


@bp.route("/course/<int:course_id>/add_assistant_from_csv", methods=["POST"])
@login_required
@roles_required(["instructor"])
def add_assistant_from_csv(course_id: int):
    """Adds multiple assistants an uploaded assistant list csv file.
    :params course_id: The course the assistants will be added to.
    """
    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)

        file: FileStorage = request.files["file"]
        if not file or not file.filename or not file.filename.endswith(".csv"):
            return redirect(request.url)
        try:
            if file and file.filename.endswith(".csv"):
                stream = io.TextIOWrapper(file.stream, encoding="utf-8")
                data: pd.DataFrame = pd.read_csv(  # type: ignore
                    stream,
                    header=0,
                    skiprows=[1, 2],
                    usecols=["Assistant", "SIS User ID"],
                    dtype=str,  # type: ignore
                )
                data["Assistant"] = data["Assistant"].str.strip()
                data[["Last Name", "First Name"]] = data["Assistant"].str.split(",")
                add_assistants_from_list(data, course_id)
        except Exception:
            return redirect(request.url)

    return redirect(url_for(".course_documents", course_id=course_id))


def create_upload_folder(course_id: int):
    """Creates a folder named after the course id within the uploads folder.
    :param course_id: name of the folder to be created
    """
    upload_path = Path(Config.FILE_STORAGE_PATH)
    if not upload_path.is_dir():
        upload_path.mkdir(parents=True, exist_ok=True)

    course_path = upload_path / str(course_id)
    if not course_path.is_dir():
        course_path.mkdir(parents=True, exist_ok=True)
