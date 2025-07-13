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
from ..api.file_parsing.file_parsing import parse_file
from ..api.embedding.embedding import embed_text
from ..db.models import add_new_document, store_segment, store_embedding, set_document_inactive

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
documents = {}

bp = Blueprint("routes", __name__)



@bp.route("/")
def course_selection():
    """Responds with a landing page where a student can select a course"""
    docs_list = os.listdir(current_app.config["UPLOAD_FOLDER"])
    for doc in docs_list:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], doc)
        docs = os.listdir(path)
        for d in docs:
            documents[os.path.join(path, d)] = True
            print(os.path.join(path, d))
            print(d)
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
    error_docstring = ""
    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)

        file: FileStorage = request.files["file"]

        if not file.filename:
            return redirect(request.url)

        if _allowed_file(file.filename) == False:
            """
            Puts an error popup when the teacher adds something bad.
            """
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
            # return render_template("documents.html", body=docstring)

        if file and _allowed_file(file.filename):
            filename: str = secure_filename(file.filename)
            new_doc_file_path = os.path.join(os.path.join(curr_path, courses[course_id]), filename)
            file.save(
                new_doc_file_path
            )
            documents[new_doc_file_path] = True
            add_new_document(new_doc_file_path, course_id)
            # Parse into segments
            segments: list[str] = parse_file(
                new_doc_file_path
            )
            for segment in segments:
                segment_id = store_segment(segment, new_doc_file_path)
                embedding = embed_text(segment)
                store_embedding(embedding, segment_id)

    docs_list = os.listdir(os.path.join(curr_path, courses[course_id]))
    doc_string = ""
    for i, doc in enumerate(docs_list):
        if documents[os.path.join(os.path.join(curr_path, courses[course_id]), doc)] == False:
            continue
        download_link = url_for(".download_file", course_id=course_id, name=doc)
        delete_link = url_for(".delete_document", course_id=course_id, filename=doc)

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


@bp.route("/course/<int:course_id>/documents/delete/<filename>", methods=["POST"])
def delete_document(course_id: int, filename: str):
    """This function deletes a file for the course
    :param course_id: The id of the course of the file to be deleted
    :param filename: Name of the file to be deleted.
    """
    curr_path = cast(str, current_app.config["UPLOAD_FOLDER"])
    file_path = os.path.join(curr_path, courses[course_id], secure_filename(filename))

    if os.path.exists(file_path):
        #os.remove(file_path)
        documents[file_path] = False
        set_document_inactive(file_path)

    return redirect(url_for(".course_documents", course_id=course_id))


@bp.route("/uploads/<int:course_id>/<name>")
def download_file(course_id: int, name: str):
    """Responds with a page of the specified document that then can be downloaded.
    :param name: The name of the file stored to be downloaded.
    :param course_id: The course id of the course the file belongs to
    """
    curr_path: str = cast(str, current_app.config["UPLOAD_FOLDER"])
    file_path = os.path.join(curr_path, courses[course_id])
    return send_from_directory(file_path, name)
