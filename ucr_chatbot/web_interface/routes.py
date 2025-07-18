from flask import Blueprint, render_template, request, jsonify
from ucr_chatbot.db.models import (
    Session,
    engine,
    Messages,
    MessageType,
    Conversations,
    Courses,
    ParticipatesIn,
)

from sqlalchemy import select, insert

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
            select(Courses)
            .join(ParticipatesIn, Courses.id == ParticipatesIn.course_id)
            .where(ParticipatesIn.email == user_email)
        )
        courses = session.execute(stmt).scalars().all()

    return render_template(
        "landing_page.html",
        courses=courses,
        "landing_page.html",
        courses=courses,
    )


@bp.route("/conversation/new/<int:course_id>/chat", methods=["GET", "POST"])
def new_conversation(course_id: int):
    """Renders the conversation page for a new conversation.

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
    """Renders the conversation page for an existing conversation.

    :param conversation_id: The id of the conversation to be displayed.
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
    """Responds with a page for course document management.

    :param course_id: The id of the course.
    """Responds with a page for course document management.

    :param course_id: The id of the course.
    """
    return render_template(
        "base.html",
        title="Course Documents",
        title="Course Documents",
        body=f"These are the documents for the course with id {course_id}",
    )
