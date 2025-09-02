from flask import (
    Blueprint,
    render_template,
    request,
    url_for,
    redirect,
    send_file,
    abort,
    flash,
    Response as FlaskResponse,
)

from sqlalchemy import select
from pathlib import Path, PurePath
import pandas as pd
import io
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_login import current_user, login_required  # type: ignore
from datetime import datetime
from ucr_chatbot.decorators import roles_required
from typing import Optional
from io import BytesIO


from ucr_chatbot.db.models import (
    Session,
    get_engine,
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
    remove_user_from_course,
    Users,
)
from ucr_chatbot.api.file_storage import get_storage_service
from ucr_chatbot.api.summary_generation import generate_usage_summary
from ucr_chatbot.api.file_parsing.file_parsing import parse_file, FileParsingError
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
    with Session(get_engine()) as session:
        user = session.query(Users).filter_by(email=email).first()
    if user is None:
        abort(404, description="User not found")
    error_msg = ""

    storage_service = get_storage_service()

    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part", "error")
            return redirect(request.url, 400)

        file: FileStorage = request.files["file"]
        if not file.filename:
            flash("No selected file", "error")
            return redirect(request.url, 400)

        filename = secure_filename(file.filename)
        file_path = Path(str(course_id)) / filename
        file_extension = file_path.suffix[1:]

        with Session(get_engine()) as session:
            if session.query(Documents).filter_by(
                file_path=str(file_path)
            ).first() or storage_service.file_exists(file_path):
                flash(
                    "A file with this name has already been uploaded for this course. Please rename the file to upload it.",
                    "error",
                )
                return redirect(request.url, code=400)

        file_data = io.BytesIO(file.stream.read())

        segments = None
        try:
            segments = parse_file(file_data, file_extension)
        except FileParsingError:
            flash("You can't upload this type of file", "error")
            return redirect(url_for(".course_documents", course_id=course_id), 400)

        add_new_document(
            str(file_path).replace(str(Path().anchor), ""),
            course_id,
        )
        for seg in segments:
            seg_id = store_segment(
                seg,
                str(file_path).replace(str(Path().anchor), ""),
            )

            embedding = embed_text(seg)
            store_embedding(embedding, seg_id)

        file_data.seek(0)
        storage_service.save_file(file_data, file_path)

        flash("File uploaded and processed successfully!", "success")
        return redirect(url_for(".course_documents", course_id=course_id))

    docs_html = ""
    active_docs = get_active_documents()
    docs_dir = PurePath(str(course_id))

    for idx, file_path in enumerate(storage_service.list_directory(docs_dir), start=1):
        if storage_service.is_directory(file_path):
            continue

        if file_path not in active_docs:
            continue

        docs_html += f"""
              <div style="margin-bottom:4px;">
                  {idx}. <a href="{url_for(".download_file", file_path=file_path)}">{file_path.name}</a>
                  <form action="{url_for(".delete_document", file_path=file_path)}" method="post" style="display:inline;">
                      <button type="submit" onclick="return confirm('Delete {file_path.name}?');">Delete</button>

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

    storage_service = get_storage_service()

    with Session(get_engine()) as session:
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

        if storage_service.file_exists(Path(file_path)):
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
    with Session(get_engine()) as session:
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

    storage_service = get_storage_service()

    return send_file(BytesIO(storage_service.get_file(path_obj).read()), path_obj.name)


@bp.route("/course/<int:course_id>/add_student", methods=["POST"])
@login_required
@roles_required(["instructor"])
def add_student(course_id: int):
    """Adds a student to the current course.
    :param course_id: The course the student will be added to.
    """
    user_email = request.form["email"]
    role = request.form.get("role", "student")  # Default to student if not provided

    add_user_to_course(user_email, course_id, role)
    return redirect(url_for(".course_documents", course_id=course_id))


@bp.route("/course/<int:course_id>/remove_student", methods=["POST"])
@login_required
@roles_required(["instructor"])
def remove_student(course_id: int):
    """Removes a student from the current course.
    :param course_id: The course the student will be removed from.
    """

    user_email = request.form["email"]
    role = request.form.get("role", "student")

    remove_user_from_course(user_email, course_id, role)
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

    with Session(get_engine()) as session:
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
            return redirect(request.url, 400)

        file: FileStorage = request.files["file"]
        if not file or not file.filename or not file.filename.endswith(".csv"):
            return redirect(request.url, 400)
        if file and file.filename.endswith(".csv"):
            stream = io.TextIOWrapper(file.stream, encoding="utf-8")

            try:
                data: pd.DataFrame = pd.read_csv(  # type: ignore
                    stream,
                    header=0,
                    skiprows=[1, 2],
                    usecols=["Student", "SIS User ID"],
                    dtype=str,  # type: ignore
                )
            except ValueError as e:
                flash(f"Invalid CSV file submitted: {e}", "error")
                return redirect(request.url, 400)
            add_students_from_list(data, course_id)

    return redirect(url_for(".course_documents", course_id=course_id))


@bp.route("/course/<int:course_id>/add_assistant", methods=["POST"])
@login_required
@roles_required(["instructor"])
def add_assistant(course_id: int):
    """Adds an assistant to the current course.
    :param course_id: The course the assistant will be added to.
    """
    user_email = request.form["email"]
    role = request.form.get("role", "assistant")

    add_user_to_course(user_email, course_id, role)
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
                add_assistants_from_list(data, course_id)
        except Exception:
            return redirect(request.url)

    return redirect(url_for(".course_documents", course_id=course_id))
