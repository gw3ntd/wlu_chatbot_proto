from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    url_for,  # ← new
    redirect,  # ← new
    send_from_directory,  # ← new
)
from werkzeug.utils import secure_filename  # ← new
from werkzeug.datastructures import FileStorage  # ← new
from sqlalchemy import select, insert
import os  # ← new
import pandas as pd
import io


from ucr_chatbot.db.models import (
    Session,
    engine,
    Messages,
    MessageType,
    Conversations,
    Courses,
    ParticipatesIn,
    Documents,
    upload_folder,
    add_new_document,
    store_segment,
    store_embedding,
    get_active_documents,
    set_document_inactive,
    add_user_to_course,
    add_students_from_list,
)

from ..api.file_parsing.file_parsing import parse_file
from ..api.embedding.embedding import embed_text

bp = Blueprint("web_routes", __name__)


def get_conv_messages(conversation_id: int):
    """Responds with all messages in requested conversation

    :param conversation_id: The id of the conversation to return messages for.
    """
    with Session(engine) as session:
        stmt = (
            select(Messages)
            .where(Messages.conversation_id == conversation_id)
            .order_by(Messages.timestamp.asc())
        )
        messages = session.execute(stmt).scalars().all()

        type_map = {
            MessageType.STUDENT_MESSAGES: "StudentMessage",
            MessageType.BOT_MESSAGES: "BotMessage",
        }
        messages_list = []
        for message in messages:
            sender = type_map.get(message.type)  # type: ignore
            message_dict = {
                "id": message.id,
                "body": message.body,
                "sender": sender,
                "timestamp": message.timestamp.isoformat(),
            }
            messages_list.append(message_dict)  # type: ignore

        return jsonify({"messages": messages_list})


def get_conversation_ids(user_email: str, course_id: int):
    """Responds with the ids of all conversations a user has with a course

    :param user_email: The id of the user the conversations belongs to
    :param courseID: The id of the course
    """

    with Session(engine) as session:
        stmt = (
            select(Conversations.id)
            .where(
                Conversations.initiated_by == "test@ucr.edu",
                Conversations.course_id == course_id,
            )
            .order_by(Conversations.id.desc())
        )
        result = session.execute(stmt).scalars().all()

    return jsonify(result)


def create_conversation(course_id: int, user_email: str, message: str):
    """Initializes a new conversation in the database


    :param courseID: The id of the course
    :param user_email: The id of the user the conversations belongs to
    :param message: the first message within the new conversation
    """

    with Session(engine) as session:
        new_conv = Conversations(course_id=course_id, initiated_by=user_email)
        session.add(new_conv)
        session.commit()

        conv_id = new_conv.id

        insert_msg = insert(Messages).values(
            body=message,
            conversation_id=conv_id,
            type=MessageType.STUDENT_MESSAGES,
            written_by=user_email,
        )
        session.execute(insert_msg)
        session.commit()
    return jsonify({"conversationId": conv_id})


def reply_conversation(conversation_id: int, user_email: str, message: str):
    """Retrieves the LLM response to a user's message

    :param conversation_id: The ID of the current conversation.
    :param user_email: The id of the user
    :param message: the user's message the LLM is responding to

    """
    _ = message
    llm_response = "LLM response"
    with Session(engine) as session:
        insert_msg = insert(Messages).values(
            body=llm_response,
            conversation_id=conversation_id,
            type=MessageType.BOT_MESSAGES,
            written_by=user_email,
        )
        session.execute(insert_msg)
        session.commit()

    return jsonify({"reply": llm_response})


def send_conversation(conversation_id: int, user_email: str, message: str):
    """Saves a new user message to the database.

    :param conversation_id: The ID of the current conversation.
    :param user_email: The id of the user
    :param message: The message to be stored
    """

    with Session(engine) as session:
        insert_msg = insert(Messages).values(
            body=message,
            conversation_id=conversation_id,
            type=MessageType.STUDENT_MESSAGES,
            written_by=user_email,
        )
        session.execute(insert_msg)
        session.commit()

    return jsonify({"status": "200"})


@bp.route("/")
def course_selection():
    """Renders the main landing page with a list of the user's courses."""
    user_email = "test@ucr.edu"
    with Session(engine) as session:
        stmt = (
            select(Courses, ParticipatesIn.role)
            .join(ParticipatesIn, Courses.id == ParticipatesIn.course_id)
            .where(ParticipatesIn.email == user_email)
        )

        courses = session.execute(stmt).all()

    return render_template(
        "landing_page.html",
        courses=courses,
    )


@bp.route("/conversation/new/<int:course_id>/chat", methods=["GET", "POST"])
def new_conversation(course_id: int):
    """Renders the conversation page for a new conversation.

    :param course_id: The id of the course for which a conversation will be initialized.
    """
    if (
        request.accept_mimetypes.accept_json
        and not request.accept_mimetypes.accept_html
    ):
        content = request.get_json()
        request_type = content["type"]
        user_email = "test@ucr.edu"

        if request_type == "ids":
            return get_conversation_ids(user_email, course_id)
        elif request_type == "create":
            return create_conversation(course_id, user_email, content["message"])

    return render_template("conversation.html", course_id=course_id)


@bp.route("/conversation/<int:conversation_id>", methods=["GET", "POST"])
def conversation(conversation_id: int):
    """Renders the conversation page for an existing conversation.
    :param conversation_id: The id of the conversation to be displayed.
    """

    if (
        request.accept_mimetypes.accept_json
        and not request.accept_mimetypes.accept_html
    ):
        content = request.get_json()
        request_type = content["type"]
        user_email = "test@ucr.edu"

        if request_type == "send":
            return send_conversation(conversation_id, user_email, content["message"])
        elif request_type == "reply":
            return reply_conversation(conversation_id, user_email, content["message"])
        elif request_type == "conversation":
            return get_conv_messages(conversation_id)
        else:
            return jsonify({"error": "Unknown request type"})

    else:
        with Session(engine) as session:
            conv = session.execute(
                select(Conversations).where(Conversations.id == conversation_id)
            ).scalar_one()
            course_id = conv.course_id

        return render_template(
            "conversation.html", conversation_id=conversation_id, course_id=course_id
        )


@bp.route("/course/<int:course_id>/documents", methods=["GET", "POST"])
def course_documents(course_id: int):
    """Renders the documents page for a course.
    :param course_id: The id of the course for which documents are being managed."""
    curr_path = upload_folder
    error_msg = ""

    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)

        file: FileStorage = request.files["file"]
        if not file.filename:
            return redirect(request.url)

        full_local_path = ""
        try:
            filename = secure_filename(file.filename)
            relative_path = os.path.join(str(course_id), filename).replace(
                os.path.sep, "/"
            )
            full_local_path = os.path.join(curr_path, relative_path)

            file.save(full_local_path)

            segments = parse_file(full_local_path)
            add_new_document(relative_path, course_id)
            for seg in segments:
                seg_id = store_segment(seg, relative_path)
                embedding = embed_text(seg)
                store_embedding(embedding, seg_id)

        except (ValueError, TypeError):
            if os.path.exists(full_local_path):
                os.remove(full_local_path)
            error_msg = "<p style='color:red;'>You can't upload this type of file</p>"

    docs_html = ""
    active_docs = get_active_documents()
    docs_dir = os.path.join(curr_path, str(course_id))
    if os.path.isdir(docs_dir):
        for idx, doc in enumerate(os.listdir(docs_dir), 1):
            file_path = os.path.join(str(course_id), secure_filename(doc)).replace(
                os.path.sep, "/"
            )
            if file_path not in active_docs:
                continue

            docs_html += f"""
              <div style="margin-bottom:4px;">
                  {idx}. <a href="{url_for(".download_file", file_path=file_path)}">{doc}</a>
                  <form action="{url_for(".delete_document", file_path=file_path)}" method="post" style="display:inline;">
                      <button type="submit" onclick="return confirm('Delete {doc}?');">Delete</button>
                  </form>
              </div>
            """

    body = error_msg + (docs_html or "No documents uploaded yet.")
    return render_template("documents.html", body=body, course_id=course_id)


@bp.route("/document/<path:file_path>/delete", methods=["POST"])
def delete_document(file_path: str):
    """Handles file deletion requests.
    :param file_path: The path of the file to be deleted."""
    file_path = file_path.replace(os.path.sep, "/")
    full_path = os.path.join(upload_folder, file_path).replace(os.path.sep, "/")

    if os.path.exists(full_path):
        # os.remove(full_path)  # physical delete optional
        set_document_inactive(file_path)

    with Session(engine) as session:
        course_id = (
            session.query(Documents).filter_by(file_path=file_path).first().course_id  # type: ignore
        )

    return redirect(url_for(".course_documents", course_id=course_id))


@bp.route("/document/<path:file_path>/download", methods=["GET"])
def download_file(file_path: str):
    """Handles file download requests.
    :param file_path: The path of the file to be downloaded."""
    directory, name = os.path.split(file_path)
    return send_from_directory(os.path.join(upload_folder, directory), name)


@bp.route("course/<int:course_id>/add_user", methods=["POST"])
def add_student(course_id: int):
    """Adds a student to the current course.
    :param course_id: The course the student will be added to."""
    user_email = request.form["email"]
    user_fname = request.form["fname"]
    user_lname = request.form["lname"]

    add_user_to_course(user_email, user_fname, user_lname, course_id, "student")
    return redirect(url_for(".course_documents", course_id=course_id))


@bp.route("course/<int:course_id>/add_from_csv", methods=["POST"])
def add_from_csv(course_id: int):
    """Adds multiple students an uploaded student list csv file.
    :params course_id: The course the students will be added to."""
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
