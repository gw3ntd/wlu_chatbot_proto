from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
    request,
    send_from_directory,
)
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from sqlalchemy.orm import Session
import os
from ..api.file_parsing.file_parsing import parse_file
from ..api.embedding.embedding import embed_text
from ..db.models import (
    engine,
    Courses,
    upload_folder,
    add_new_document,
    store_segment,
    store_embedding,
    get_active_documents,
    set_document_inactive,
    Documents,
)


bp = Blueprint("routes", __name__)


@bp.route("/")
def course_selection():
    """Responds with a landing page where a student can select a course"""
    body_text = ""
    with Session(engine) as session:
        courses = session.query(Courses)
    for course in courses:
        body_text += f'Select your course. <a href="{url_for(".new_conversation", course_id=course.id)}"> {course.name} </a> &emsp; Upload documents for a course: <a href="{url_for(".course_documents", course_id=course.id)}"> {course.name} </a> <br/>'
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
    with Session(engine) as session:
        course = session.query(Courses).filter_by(id=course_id).first()

    curr_path: str = upload_folder

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
                os.path.join(curr_path, str(getattr(course, "id"))), filename
            )
            file.save(new_doc_file_path)
            # Parse into segments
            segments: list[str] = parse_file(new_doc_file_path)
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

    docs_list = os.listdir(os.path.join(curr_path, str(getattr(course, "id"))))
    doc_string = ""
    active_documents: list[str] = get_active_documents()
    for i, doc in enumerate(docs_list):
        if (
            os.path.join(os.path.join(curr_path, str(getattr(course, "id"))), doc)
            not in active_documents
        ):
            continue

        file_path = os.path.join(
            curr_path, str(getattr(course, "id")), secure_filename(doc)
        )
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
    if os.path.exists(file_path):
        # os.remove(file_path)
        set_document_inactive(file_path)

    course_id = 0
    with Session(engine) as session:
        course_id = getattr(
            session.query(Documents).filter_by(file_path=file_path).first(), "course_id"
        )

    return redirect(url_for(".course_documents", course_id=course_id))


@bp.route("document/<string:file_path>/download", methods=["GET"])
def download_file(file_path: str):
    """Responds with a page of the specified document that then can be downloaded.
    :param file_path: The path of the file stored to be downloaded.
    """
    print(file_path)
    path_parts = file_path.split(os.sep)
    print(path_parts)
    directory = ""
    name = ""
    for i, part in enumerate(path_parts):
        if i == (len(path_parts) - 1):
            name = part
            break
        directory += part + os.sep
    print(directory)
    print(name)
    return send_from_directory(directory, name)
