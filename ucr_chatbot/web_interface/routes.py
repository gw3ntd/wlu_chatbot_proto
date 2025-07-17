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
from sqlalchemy.orm import Session
import os
from typing import cast
from ..api.file_parsing.file_parsing import parse_file
from ..api.embedding.embedding import embed_text
from ..db.models import *

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
documents = {}


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


@bp.route("/course/<int:course_id>/documents", methods=["GET", "POST"])
def course_documents(course_id: int):
    """Responds with a page where a course administrator can add more documents
    to the course for use by the retrieval-augmented generation system.
    :param course_id: The id of the course for which a conversation will be initialized.
    """
    curr_path: str = cast(str, current_app.config["UPLOAD_FOLDER"])
    active_documents: list[str] = get_active_documents()
    for active_document in active_documents:
        documents[active_document] = True
    error_docstring = ""
    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)

        file: FileStorage = request.files["file"]

        if not file.filename:
            return redirect(request.url)

        new_doc_file_path = ""
        try:
            filename: str = secure_filename(file.filename)
            new_doc_file_path = os.path.join(
                os.path.join(curr_path, courses[course_id]), filename
            )
            file.save(new_doc_file_path)
            # Parse into segments
            segments: list[str] = parse_file(new_doc_file_path)
            documents[new_doc_file_path] = True
            add_new_document(new_doc_file_path, course_id)
            for segment in segments:
                # print(segment)
                # embed_text(segment)
                segment_id = store_segment(segment, new_doc_file_path)
                embedding = embed_text(segment)
                store_embedding(embedding, segment_id)
        except (ValueError, TypeError) as e:
            print(f"Error: {e}")
            if os.path.exists(new_doc_file_path):
                os.remove(new_doc_file_path)
            error_docstring = """
            <div id="error-popup" style="display: block;">
                <h3>Error!</h3>
                <p id="error-message">You can't upload this type of file</p>
                <button id="close-popup">Close</button>
            </div>
            <script>
                document.addEventListener("DOMContentLoaded", function() {
                    const popup = document.getElementById("error-popup");
                    const closeBtn = document.getElementById("close-popup");

                    if (closeBtn && popup) {
                    closeBtn.addEventListener("click", function() {
                        popup.style.display = "none";
                        popup.parentNode.removeChild(popup);
                    });
                }
            });
        </script>
        """

    docs_list = os.listdir(os.path.join(curr_path, courses[course_id]))
    doc_string = ""
    for i, doc in enumerate(docs_list):
        if (
            documents[os.path.join(os.path.join(curr_path, courses[course_id]), doc)]
            == False
        ):
            continue
        
        file_path = os.path.join(curr_path, courses[course_id], secure_filename(doc))
        download_link = url_for(".download_file", file_path=file_path)
        delete_link = url_for(".delete_document", file_path=file_path)

        doc_string += f'''
            <div style="margin-bottom: 5px;">
                    <span style="display: inline-block; width: 25px;">{i + 1}.</span> 
                    <a href="{download_link}" style="display: inline-block; margin-right: 10px;">{doc}</a> 
                    <form action="{delete_link}" method="post" style="display: inline-block;">
                        <button type="submit" onclick="return confirm('Are you sure you want to delete the file?');">Delete</button>
                    </form>
                </div>
        '''

    doc_string = error_docstring + doc_string
    return render_template("documents.html", body=doc_string)


@bp.route("/document/<string:file_path>/delete", methods=["POST"])
def delete_document(file_path: str):
    """This function deletes a file for the course
    :param file_path: Path of the file to be deleted.
    """
    active_documents: list[str] = get_active_documents()
    for active_document in active_documents:
        documents[active_document] = True

    if os.path.exists(file_path):
        # os.remove(file_path)
        documents[file_path] = False
        set_document_inactive(file_path)

    course_id = 0
    with Session(engine) as session:
        course_id = getattr(session.query(Documents).filter_by(file_path=file_path).first(), "course_id")

    print(course_id)
    return redirect(url_for(".course_documents", course_id=course_id))


@bp.route("document/<string:file_path>/download")
def download_file(file_path: str):
    """Responds with a page of the specified document that then can be downloaded.
    :param file_path: The path of the file stored to be downloaded.
    """
    print(file_path)
    path_parts = file_path.split("\\")
    print(path_parts)
    directory = ""
    name = ""
    for i, part in enumerate(path_parts):
        if i == (len(path_parts)-1):
            name = part
            break
        directory += part + "/"
    print(directory)
    print(name)
    return send_from_directory(directory, name)
