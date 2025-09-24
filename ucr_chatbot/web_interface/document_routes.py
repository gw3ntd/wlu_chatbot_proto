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

from werkzeug.datastructures import FileStorage

from pydantic import BaseModel as PydanticModel

from ucr_chatbot.decorators import roles_required
from ucr_chatbot.db.models import Session, get_engine, Document, Segment, Embedding
from ucr_chatbot.api.file_storage import get_storage_service
from ucr_chatbot.api.file_parsing import parse_file, FileParsingError
from ucr_chatbot.api.embedding import embed_text
from ucr_chatbot.api.hashing import hash_bytes

bp = Blueprint("document_routes", __name__)


def course_from_document_in_url(kwargs: dict[str, Any]) -> Optional[int]:
    """Gets the course_id from the file_path in the url."""
    with Session(get_engine()) as sess:
        doc = sess.get(Document, kwargs["document_id"])
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
    data = PostDocumentRequest.model_validate(request.form.to_dict())
    course_id = course_from_form({})
    storage_service = get_storage_service()

    if "file" not in request.files:
        flash("No file part", "error")
        return redirect(request.referrer, 400)

    file: FileStorage = request.files["file"]
    if not file.filename:
        flash("No selected file", "error")
        return redirect(request.referrer, 400)

    file_data = io.BytesIO(file.stream.read())
    file_hash = hash_bytes(file_data)

    file_extension = PurePath(file.filename).suffix[1:]

    with Session(get_engine()) as session:
        document = (
            session.query(Document)
            .filter_by(
                file_hash=file_hash,
                course_id=course_id,
            )
            .first()
        )
        if document:
            flash(
                f"An identical file, '{document.name}', has already been uploaded for this course.",
                "error",
            )
            return redirect(request.referrer or "/", code=400)

    segments = None
    file_data.seek(0)
    try:
        segments = parse_file(file_data, file_extension)
    except FileParsingError:
        flash("You can't upload this type of file", "error")
        return redirect(request.referrer or "/", 400)

    with Session(get_engine()) as session:
        document = Document(
            name=data.name,
            file_hash=file_hash,
            course_id=course_id,
            file_extension=file_extension,
        )
        session.add(document)
        session.flush()
        for seg in segments:
            segment = Segment(text=seg, document_id=document.id)
            session.add(segment)
            session.flush()
            session.add(Embedding(vector=embed_text(seg), segment_id=segment.id))
        session.commit()

        file_path = document.full_file_path

    file_data.seek(0)
    storage_service.save_file(file_data, file_path)

    flash("File uploaded and processed successfully!", "success")
    return redirect(request.referrer or "/")


@bp.route("/document/<int:document_id>", methods=["DELETE"])
@login_required
@roles_required(["instructor"], course_from_document_in_url)
def delete_document(document_id: int):
    """Deletes a document"""
    with Session(get_engine()) as session:
        document = session.get(Document, document_id)
        if document is None:
            abort(404)

        full_path = document.full_file_path
        session.delete(document)
        session.commit()

    storage_service = get_storage_service()

    storage_service.delete_file(full_path)

    return "", 204


@bp.route("/document/<int:document_id>", methods=["GET"])
@login_required
@roles_required(["instructor"], course_from_document_in_url)
def get_document(document_id: str):
    """Delivers a file."""
    with Session(get_engine()) as session:
        document = session.get(Document, document_id)
        if document is None:
            abort(404)

        document_name = document.name_with_extension
        file_path = document.full_file_path
    storage_service = get_storage_service()
    return send_file(
        io.BytesIO(storage_service.get_file(file_path).read()), document_name
    )


class PostDocumentRequest(PydanticModel):
    name: str
