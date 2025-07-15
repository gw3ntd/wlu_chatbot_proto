from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
    request,
    send_from_directory,
)
from ucr_chatbot.db.models import *
from sqlalchemy import select, insert


bp = Blueprint("routes", __name__)

user_email = "test@ucr.edu"


@bp.route("/")
def course_selection():
    print("web_interface")
    with Session(engine) as session:
        stmt = (
            select(Courses)
            .join(ParticipatesIn, Courses.id == ParticipatesIn.course_id)
            .where(ParticipatesIn.email == user_email)
        )
        result = session.execute(stmt)

        courses = []
        for row in result:
            courses.append(row[0])

    return render_template(
        "landing_page.html",
        courses=courses,
    )


@bp.route("/new_conversation/<int:course_id>/chat")
def new_conversation(course_id: int):
    """Redirects to a page with a new conversation for a course.
    :param course_id: The id of the course for which a conversation will be initialized.
    """

    return render_template("conversation.html")


@bp.route("/conversation/<int:conversation_id>")
def conversation(conversation_id: int):
    """Responds with page where a student can interact with a chatbot for a course.

    :param conversation_id: The id of the conversation to be send back to the user.
    """
    print("web con")
    return render_template(
        "conversation.html",
        title="Landing Page",
        body=f"Chat with me about the course2 for which the conversation with id {conversation_id} exists.",
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

        full_local_path = ""
        try:
            filename: str = secure_filename(file.filename)

            relative_doc_path = os.path.join(str(course_id), filename).replace(
                os.path.sep, "/"
            )
            print(relative_doc_path)
            full_local_path = os.path.join(curr_path, relative_doc_path)
            file.save(full_local_path)
            # Parse into segments
            segments: list[str] = parse_file(full_local_path)
            add_new_document(relative_doc_path, course_id)
            for segment in segments:
                # print(segment)
                # embed_text(segment)
                segment_id = store_segment(segment, relative_doc_path)
                embedding = embed_text(segment)
                store_embedding(embedding, segment_id)
        except (ValueError, TypeError) as e:
            print(f"Error: {e}")
            if os.path.exists(full_local_path):
                os.remove(full_local_path)
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
    index = 0
    for doc in docs_list:
        file_path = os.path.join(
            str(getattr(course, "id")), secure_filename(doc)
        ).replace(os.path.sep, "/")
        if file_path not in active_documents:
            continue

        download_link = url_for(".download_file", file_path=file_path)
        delete_link = url_for(".delete_document", file_path=file_path)

        doc_string += f'''
            <div style="margin-bottom: 5px;">
                    <span style="display: inline-block; width: 25px;">{index + 1}.</span> 
                    <a href="{download_link}" style="display: inline-block; margin-right: 10px;">{doc}</a> 
                    <form action="{delete_link}" method="post" style="display: inline-block;">
                        <button type="submit" onclick="return confirm('Are you sure you want to delete the file?');">Delete</button>
                    </form>
                </div>
        '''
        index += 1

    doc_string = error_docstring + doc_string
    return render_template("documents.html", body=doc_string)


@bp.route("/document/<path:file_path>/delete", methods=["POST"])
def delete_document(file_path: str):
    """This function deletes a file for the course
    :param file_path: Path of the file to be deleted.
    """
    file_path = file_path.replace(os.path.sep, "/")
    full_path = os.path.join(upload_folder, file_path).replace(os.path.sep, "/")
    if os.path.exists(full_path):
        # os.remove(file_path)
        set_document_inactive(file_path)
    print(file_path)

    course_id = 0
    with Session(engine) as session:
        course_id = getattr(
            session.query(Documents).filter_by(file_path=file_path).first(), "course_id"
        )

    return redirect(url_for(".course_documents", course_id=course_id))


@bp.route("document/<path:file_path>/download", methods=["GET"])
def download_file(file_path: str):
    """Responds with a page of the specified document that then can be downloaded.
    :param file_path: The path of the file stored to be downloaded.
    """
    directory, name = os.path.split(file_path)
    print(os.path.join(upload_folder, directory))
    print(name)
    return send_from_directory(os.path.join(upload_folder, directory), name)
