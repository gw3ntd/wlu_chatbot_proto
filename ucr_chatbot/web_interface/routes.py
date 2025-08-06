from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    url_for,
    redirect,
    send_from_directory,
    session,
    abort,
    flash,
    current_app,
    Response as FlaskResponse,
    make_response,
)

from sqlalchemy import select, insert, func
from pathlib import Path
import pandas as pd
import io
import json
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from werkzeug.security import check_password_hash
from flask_login import current_user, login_required, login_user, logout_user  # type: ignore
from datetime import datetime, timedelta, timezone
from ucr_chatbot.decorators import roles_required
from ucr_chatbot.api.language_model.response import client as response_client
from ucr_chatbot.api.context_retrieval.retriever import retriever
from typing import cast, Union, Any, Dict, Mapping, List, Optional


from ucr_chatbot.db.models import (
    Session,
    engine,
    Messages,
    MessageType,
    Conversations,
    Courses,
    ParticipatesIn,
    Documents,
    References,
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

# from ucr_chatbot.web_interface.routes.auth import get_google_auth
# from .auth import get_google_auth

from ..api.file_parsing.file_parsing import parse_file
from ..api.embedding.embedding import embed_text

bp = Blueprint("web_routes", __name__)

SYSTEM_PROMPT = """# Main directive
You are a helpful student tutor for a university computer science course. You must assist students in their learning by answering question in a didactically useful way. You should only answer questions if you are certain that you know the correct answer.
You will be given context that may or may not be useful for answering the student's question followed by the question. Again, only answer the question if you are certain that you have a correct answer. The conversation history for the last 10 messages is also provided. 
Ever explicitly say that you got information from the context or the references/numbers they come from, or tell students to reference document numbers. Only answer the students questions as if the information is coming from you.
Your main priority is being a tutor, and instead of giving direct answers most of the time, focus on teaching students and leading them to the answer themselves.

If the context is not relevant, or if it is not a follow up question, then you should tell the student, "I cannot find any relevant course materials to help answer your question."

## Context
{context}

## History
{history}

## Question
{question}
"""


@bp.route("/")
def home():
    """Login page for the user. If the user is already
    logged in, they are redirected to the dashboard

    :return: a redirect response to the dashboard or the login page
    :rtype: flask.Response
    """
    if current_user.is_authenticated:
        return redirect(url_for("web_routes.course_selection"))
    return render_template("index.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Checks if the user has valid login credentials. If they do, the
    user is successfully logged in and redirected to the dashboard

    :return: a redirect response to the dashboard or the login page
    :rtype: flask.Response
    """
    # get_flashed_messages()  # clearing flash() messages
    config = cast(Mapping[str, Any], current_app.config)
    max_attempts = cast(int, config.get("MAX_LOGIN_ATTEMPTS", 3))
    cooldown_minutes = 5

    now = datetime.now(timezone.utc)

    last_attempt_time = session.get("last_login_attempt_time")
    if last_attempt_time:
        last_attempt_time = datetime.fromisoformat(last_attempt_time)
        if now - last_attempt_time > timedelta(minutes=cooldown_minutes):
            session["login_attempts"] = 0

    if session.get("login_attempts", 0) >= max_attempts:
        flash("Too many failed login attempts. Please try again later", "error")
        return render_template("index.html")

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        with Session(engine) as db_session:
            user: Users | None = db_session.query(Users).filter_by(email=email).first()

        if user and check_password_hash(cast(str, user.password_hash), password):
            login_user(user)
            session.pop("login_attempts", None)
            session.pop("last_login_attempt_time", None)
            return redirect(
                request.args.get("next") or url_for("web_routes.course_selection")
            )
        else:
            session["login_attempts"] = session.get("login_attempts", 0) + 1
            session["last_login_attempt_time"] = now.isoformat()
            remaining = max_attempts - session["login_attempts"]
            flash(
                f"Invalid email or password. {remaining} attempt(s) remaining.", "error"
            )
    rendered_template = render_template("index.html")
    response = make_response(rendered_template)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@bp.route("/logout")
@login_required
def logout():
    """The user is sucessfully logged out and redirected to
    the home page

    :return: a redirect response to the home page
    :rtype: flask.Response
    """
    logout_user()
    return redirect(url_for("web_routes.home"))


@bp.route("/login/google")
def login_google() -> Union[FlaskResponse, tuple[str, int]]:
    """This function starts the Google OAuth login process for
    the user. It will either redirect the user to the Google OAuth
    authorization endpoint or, if an error occurs, it returns a 500
    error response.

    :return: a redirect response to Google authorization URL or
    a tuple containing an error message
    :rtype: Response | tuple[str, int]
    """
    try:
        config = cast(Mapping[str, Any], current_app.config)
        max_attempts = cast(int, config.get("MAX_LOGIN_ATTEMPTS", 3))
        cooldown_minutes = 5

        now = datetime.now(timezone.utc)
        last_attempt_time = session.get("last_login_attempt_time")

        if last_attempt_time:
            last_attempt_time = datetime.fromisoformat(last_attempt_time)
            if now - last_attempt_time > timedelta(minutes=cooldown_minutes):
                session["login_attempts"] = 0

        if session.get("login_attempts", 0) >= max_attempts:
            flash("Too many failed login attempts. Please try again later", "error")
            return cast(FlaskResponse, redirect(url_for("web_routes.login")))

        google = current_app.oauth.google  # type: ignore
        redirect_uri = url_for("web_routes.authorize_google", _external=True)
        return google.authorize_redirect(redirect_uri)  # type: ignore
    except Exception as e:
        import traceback

        traceback.print_exc()
        return f"<pre>Error occurred during login:<br>{str(e)}</pre>", 500


@bp.route("/authorize/google")
def authorize_google():
    """Google OAuth user verification. If the user is verified,
    they are logged in and redirected to the dashboard endpoint. If they
    can't be verified, an error message pops up.

    :return: redirects user to the dashboard on success or returns an error
    :rtype: Response | tuple[str, int]
    """
    try:
        if "code" not in request.args:
            flash("Google authorization failed: No code received", "error")
            return redirect(url_for("web_routes.login"))

        google = current_app.oauth.google  # type: ignore
        token = google.authorize_access_token()  # type: ignore
        if not token:
            flash("Google authorization failed: No token received", "error")
            return redirect(url_for("web_routes.login"))

        userinfo_endpoint = google.server_metadata["userinfo_endpoint"]  # type: ignore
        resp = google.get(userinfo_endpoint)  # type: ignore
        resp.raise_for_status()  # type: ignore
        user_info = cast(Dict[str, Any], resp.json())  # type: ignore

        email: str = user_info["email"]
        with Session(engine) as db_session:
            # user = db_session.query(Users).filter_by(email=email).first()
            user = (
                db_session.query(Users).filter(func.lower(Users.email) == email).first()
            )
            if not user:
                config = cast(Mapping[str, Any], current_app.config)
                session["login_attempts"] = session.get("login_attempts", 0) + 1
                session["last_login_attempt_time"] = datetime.now(
                    timezone.utc
                ).isoformat()
                remaining: int = (
                    cast(int, config.get("MAX_LOGIN_ATTEMPTS", 3))
                    - session["login_attempts"]
                )
                flash(
                    f"Access denied: This email is not authorized. {remaining} attempt(s) remaining.",
                    "error",
                )
                return redirect(url_for("web_routes.login"))

            login_user(user)  # Log the user in
            session.pop("login_attempts", None)
            session.pop("last_login_attempt_time", None)
            # session.regenerate()
        return redirect(url_for("web_routes.course_selection"))
    except Exception as e:
        import traceback

        traceback.print_exc()
        flash(f"Authorization error: {str(e)}", "error")
        return f"<pre>Authorization error:<br>{str(e)}</pre>", 500


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
            MessageType.ASSISTANT_MESSAGES: "AssistantMessage",
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
                Conversations.initiated_by == user_email,
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


def generate_response(
    prompt: str,
    conversation_id: int,
    stream: bool = False,
    history: int = 5,
    temperature: float = 1.0,
    max_tokens: int = 5000,
    stop_sequences: list[str] | None = None,
) -> FlaskResponse:
    """Generates RAG assisted response for the reply in a user conversation

    :param prompt: The user defined query for the LLM
    :param conversation_id: The ID of the current conversation.
    :param stream: Single response or continuous conversation
    :param history: The number of student/bot history responses included in the prompt
    :param temperature: How creative the response is
    :param max_tokens: The maximum number of tokens that can be input to a single query
    :stop_sequences: A list of stop sequences for the prompt

    :return: Response of the LLM and its sources
    """

    if stop_sequences is None:
        stop_sequences = []

    with Session(engine) as session:
        course_id_row = (
            session.query(Conversations).filter_by(id=conversation_id).first()
        )

    if course_id_row is None:
        return jsonify(
            {
                "text": "An error has occured.",
                "sources": [{"source_id": 0}],
                "conversation_id": conversation_id,
            }
        )

    course_id = course_id_row.course_id

    segments = retriever.get_segments_for(prompt, course_id=course_id, num_segments=10)  # type: ignore
    context = "\n".join(
        # Assuming each 's' object has 'segment_id' and 'text' attributes
        map(lambda s: f"Reference number: {s.id}, text: {s.text}", segments)  # type: ignore
    )

    prompt_with_context = SYSTEM_PROMPT.format(
        context=context,
        question=prompt,
        history=get_conv_messages(conversation_id).get_json()["messages"][
            -(history * 2) :
        ],
    )

    generation_params = {  # type: ignore
        "prompt": prompt_with_context,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stop_sequences": stop_sequences,
    }

    if stream:
        # Define a generator function to format the stream as Server-Sent Events (SSE)
        def stream_generator():
            for chunk in response_client.stream_response(**generation_params):  # type: ignore
                # Format each chunk as a Server-Sent Event
                yield f"data: {json.dumps({'text': chunk})}\n\n"

        return FlaskResponse(stream_generator(), mimetype="text/event-stream")
    else:
        response_text = response_client.get_response(**generation_params)  # type: ignore

        # Dynamically create the list of source IDs
        sources = [{"segment_id": s.id} for s in segments]  # type: ignore

        return jsonify(
            {
                "text": response_text,
                "sources": sources,
                "conversation_id": conversation_id,
            }
        )


def reply_conversation(conversation_id: int, user_email: str, message: str):
    """Retrieves the LLM response to a user's message

    :param conversation_id: The ID of the current conversation.
    :param user_email: The id of the user
    :param message: the user's message the LLM is responding to

    """
    llm_response_data = generate_response(
        prompt=message, conversation_id=conversation_id, stream=False, history=5
    ).get_json()
    llm_response = llm_response_data["text"]
    with Session(engine) as session:
        insert_msg = (
            insert(Messages)
            .values(
                body=llm_response,
                conversation_id=conversation_id,
                type=MessageType.BOT_MESSAGES,
                written_by=user_email,
            )
            .returning(Messages.id)
        )
        result = session.execute(insert_msg)
        message_id = result.scalar_one()
        session.commit()
        if message_id:
            for seg in llm_response_data["sources"]:
                insert_ref = insert(References).values(
                    message=message_id,
                    segment=seg["segment_id"],
                )
                session.execute(insert_ref)
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


@bp.route("/course_selection")
@login_required
def course_selection():
    """Renders the main landing page with a list of the user's courses."""
    user_email = current_user.email
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
        email=current_user.email,
    )


@bp.route("/conversation/new/<int:course_id>/chat", methods=["GET", "POST"])
@login_required
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
        user_email = current_user.email

        if request_type == "ids":
            return get_conversation_ids(user_email, course_id)
        elif request_type == "create":
            return create_conversation(course_id, user_email, content["message"])

    return render_template("conversation.html", course_id=course_id)


@bp.route("/conversation/<int:conversation_id>", methods=["GET", "POST"])
@login_required
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
        user_email = current_user.email

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


def generate_conversation_summary(
    conversation_id: int,
    time_start: Optional[datetime],
    time_end: Optional[datetime],
) -> str:
    """Generates a  summary of all student-chatbot interactions that occurred in a single conversation between a start and end time."""
    with Session(engine) as session:
        total_messages: List[str] = []

        stmt = (
            select(Messages.type, Messages.body)
            .join(Conversations, Messages.conversation_id == Conversations.id)
            .where(Conversations.id == conversation_id)
        )
        if time_start:
            stmt = stmt.where(Messages.timestamp > time_start)
        if time_end:
            stmt = stmt.where(Messages.timestamp < time_end)

        stmt = stmt.order_by(Messages.timestamp)

        messages = session.execute(stmt).all()

        type_map = {
            MessageType.STUDENT_MESSAGES: "StudentMessage",
            MessageType.BOT_MESSAGES: "BotMessage",
            MessageType.ASSISTANT_MESSAGES: "AssistantMessage",
        }

        for message in messages:
            total_messages.append(f"{type_map.get(message.type)}: {message.body}")

        total_messages_txt = "\n".join(total_messages)

        prompt = f"""These are all of the messages within one conversation between a student and a AI chatbot tutor. Create a summary of this conversation, including topics discussed and student performance.
        Also include a section summarising topics being discussed where students talked to a human assistant. Messages labeled 'AssistantMessage' represent human assistants {total_messages_txt}"""
        response = response_client.get_response(prompt)

        return response


def generate_usage_summary(
    course_id: int,
    time_start: Optional[datetime],
    time_end: Optional[datetime],
    course_name: str,
) -> str:
    """Generates a summary of all student-chatbot interactions that occurred between a start and end time."""

    with Session(engine) as session:
        stmt = (
            select(func.count(func.distinct(Messages.written_by)))
            .join(Conversations, Messages.conversation_id == Conversations.id)
            .where(Conversations.course_id == course_id)
        )

        if time_start:
            stmt = stmt.where(Messages.timestamp > time_start)
        if time_end:
            stmt = stmt.where(Messages.timestamp < time_end)

        student_count = session.execute(stmt).scalar_one()

        stmt = (
            select(func.count(func.distinct(Messages.conversation_id)))
            .join(Conversations, Messages.conversation_id == Conversations.id)
            .where(Conversations.course_id == course_id)
        )

        if time_start:
            stmt = stmt.where(Messages.timestamp > time_start)
        if time_end:
            stmt = stmt.where(Messages.timestamp < time_end)

        conv_count = session.execute(stmt).scalar_one()

        stmt = (
            select(func.distinct(Messages.conversation_id))
            .join(Conversations, Messages.conversation_id == Conversations.id)
            .where(Conversations.course_id == course_id)
        )
        if time_start:
            stmt = stmt.where(Messages.timestamp > time_start)
        if time_end:
            stmt = stmt.where(Messages.timestamp < time_end)

        conversation_ids = session.execute(stmt).scalars().all()

        total_messages: List[str] = []
        for conv_id in conversation_ids:
            total_messages.append(
                generate_conversation_summary(conv_id, time_start, time_end)
            )

        total_messages_txt = "\n".join(total_messages)

    prompt = f"""These are all of the messages that students have been having with a AI chatbot for help with a computer science course. 
                Generate a report for this course's instructor summarising students\' interactions with the chatbot, highlighting common questions and students\' strengths and weaknesses
                Here are the all student chatbot messages {total_messages_txt}
                Do not include any information of chatbot performance, or include recommendations for the professor
                Do not focus too much on specific/invidual interactions between a student and the chatbot. 
                Focus more higher level, what topics are being discussed and with what frequency, which topics are students struggling at, how are they struggling.
                Do not include a title for the report.
                Also include a section discussing instances where conversations involved the student talking to a human assistant.
                """

    response = response_client.get_response(prompt)

    if time_start and time_end:
        title = f"## {course_name} Chatbot Interaction Report ({time_start.date()} - {time_end.date()})\n\n"
    elif time_start:
        title = f"## {course_name} Chatbot Interaction Report ({time_start.date()} - Present)\n\n"
    else:
        title = f"## {course_name} Chatbot Interaction Report\n\n"

    summary = (
        title
        + "Active Students: "
        + str(student_count)
        + "\nTotal Conversations: "
        + str(conv_count)
        + "\n\n"
        + response
    )

    return summary


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
    role = request.form.get("role", "assistant")  # Default to assistant if not provided

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
