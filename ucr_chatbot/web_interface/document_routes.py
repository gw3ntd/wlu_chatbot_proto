from typing import Optional, cast, Any
import io
from pathlib import PurePath


from flask import (
    Blueprint,
    request,
    send_file,
    abort,
    redirect,
    flash,
)
from flask_login import login_required  # type: ignore

from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from ucr_chatbot.decorators import roles_required
from ucr_chatbot.db.models import Session, get_engine, Document, Segment
from ucr_chatbot.api.file_storage import get_storage_service
from ucr_chatbot.api.file_parsing import parse_file, FileParsingError

bp = Blueprint("document_routes", __name__)


def course_from_document_in_url(kwargs: dict[str, Any]) -> Optional[int]:
    """Gets the course_id from the file_path in the url."""
    with Session(get_engine()) as sess:
        doc = sess.get(Document, kwargs["file_path"])
        if not doc:
            return None
        return cast(int, doc.course_id)


def course_from_query_parameter(_: dict[str, Any]) -> Optional[int]:
    """"""
    course_id = request.args.get("course_id")
    if course_id is None:
        return None
    return int(course_id)


def course_from_form(_: dict[str, Any]) -> int:
    """"""
    return int(request.form.to_dict()["course_id"])


@bp.route("/documents", methods=["POST"])
@login_required
@roles_required(["instructor"], course_from_form)
def post_document():
    """Creates a document"""

    course_id = course_from_form({})
    storage_service = get_storage_service()

    if "file" not in request.files:
        flash("No file part", "error")
        return redirect(request.referrer, 400)

    file: FileStorage = request.files["file"]
    if not file.filename:
        flash("No selected file", "error")
        return redirect(request.referrer, 400)

    filename = secure_filename(file.filename)
    file_path = PurePath(str(course_id)) / filename
    file_extension = file_path.suffix[1:]

    with Session(get_engine()) as session:
        if session.query(Document).filter_by(
            file_path=str(file_path)
        ).first() or storage_service.file_exists(file_path):
            flash(
                "A file with this name has already been uploaded for this course. Please rename the file to upload it.",
                "error",
            )
            return redirect(request.referrer, code=400)

    file_data = io.BytesIO(file.stream.read())

    segments = None
    try:
        segments = parse_file(file_data, file_extension)
    except FileParsingError:
        flash("You can't upload this type of file", "error")
        return redirect(request.referrer or "/", 400)

    with Session(get_engine()) as session:
        session.add(
            Document(
                file_path=str(file_path),
                course_id=course_id,
            )
        )
        for seg in segments:
            session.add(Segment(text=seg, document_id=str(file_path)))
        session.commit()

    file_data.seek(0)
    storage_service.save_file(file_data, file_path)

    flash("File uploaded and processed successfully!", "success")
    return redirect(request.referrer or "/")


@bp.route("/document/<path:file_path>", methods=["DELETE"])
@login_required
@roles_required(["instructor"], course_from_document_in_url)
def delete_document(file_path: str):
    """Deletes a document"""
    with Session(get_engine()) as session:
        document = session.query(Document).filter_by(file_path=file_path).first()
        if document is None:
            abort(404)

        document.is_active = False  # type: ignore
        session.commit()

    return "", 204


@bp.route("/document/<path:file_path>", methods=["GET"])
@login_required
@roles_required(["instructor"], course_from_document_in_url)
def get_document(file_path: str):
    """Delivers a file."""
    path_obj = PurePath(file_path)
    storage_service = get_storage_service()
    return send_file(
        io.BytesIO(storage_service.get_file(path_obj).read()), path_obj.name
    )
