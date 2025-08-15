from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    Response as FlaskResponse,
)

from sqlalchemy import select, insert
import json
from flask_login import current_user, login_required  # type: ignore
from ucr_chatbot.api.language_model.response import client as response_client
from ucr_chatbot.api.context_retrieval.retriever import retriever


from ucr_chatbot.db.models import (
    Session,
    engine,
    Messages,
    MessageType,
    Conversations,
    ParticipatesIn,
    References,
)


bp = Blueprint("conversation_routes", __name__)

SYSTEM_PROMPT = """# Main directive
You are a helpful student tutor for a university computer science course. You must assist students in their learning by answering question in a didactically useful way. You should only answer questions if you are certain that you know the correct answer.
You will be given context that may or may not be useful for answering the student's question followed by the question. Again, only answer the question if you are certain that you have a correct answer. The conversation history for the last 10 messages is also provided. 
Never explicitly say that you got information from the context or the references/numbers they come from, or tell students to reference document numbers. Only answer the students questions as if the information is coming from you.
Your main priority is being a tutor, and instead of giving direct answers most of the time, focus on teaching students and leading them to the answer themselves.

If the context is not relevant, or if it is not a follow up question, then you should tell the student, "I cannot find any relevant course materials to help answer your question."

## Context
{context}

## History
{history}

## Question
{question}
"""


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
        elif request_type == "redirect":
            return conversation_redirect_status(conversation_id)
        else:
            return jsonify({"error": "Unknown request type"})

    else:
        with Session(engine) as session:
            conv = session.execute(
                select(Conversations).where(Conversations.id == conversation_id)
            ).scalar_one()
            course_id = conv.course_id

        return render_template(
            "conversation.html",
            conversation_id=conversation_id,
            course_id=course_id,
        )


@bp.route("/conversation/<int:conversation_id>/redirect", methods=["POST"])
@login_required
def redirect_conversation(conversation_id: int):
    """Redirects a conversation to an assistant for manual handling.
    :param conversation_id: The ID of the conversation to redirect.
    """
    user_email = current_user.email

    with Session(engine) as session:
        conversation = (
            session.query(Conversations).filter_by(id=conversation_id).first()
        )
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404

        # Check if user is the initiator or has permission
        if conversation.initiated_by != user_email:
            # Check if user is an assistant for this course
            participation = (
                session.query(ParticipatesIn)
                .filter_by(
                    email=user_email, course_id=conversation.course_id, role="assistant"
                )
                .first()
            )
            if not participation:
                return jsonify({"error": "Unauthorized"}), 403

        # Mark conversation as redirected but not resolved
        try:
            conversation.redirected = True  # type: ignore
            session.commit()
            # flash("Your conversation is now visible to assistants, the AI chat bot is now disabled for this conversation.")
        except Exception as e:
            # If redirected column doesn't exist, just return success
            print(f"Warning: redirected column not found, skipping redirect flag: {e}")
            session.rollback()

        return jsonify(
            {"status": "redirected", "message": "Conversation redirected to assistant"}
        )


@bp.route("/conversation/<int:conversation_id>/resolve", methods=["POST"])
@login_required
def resolve_conversation(conversation_id: int):
    """Marks a conversation as resolved.
    :param conversation_id: The ID of the conversation to resolve.
    """
    user_email = current_user.email

    with Session(engine) as session:
        conversation = (
            session.query(Conversations).filter_by(id=conversation_id).first()
        )
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404

        # Check if user is the initiator or has permission
        if conversation.initiated_by != user_email:
            # Check if user is an assistant for this course
            participation = (
                session.query(ParticipatesIn)
                .filter_by(
                    email=user_email, course_id=conversation.course_id, role="assistant"
                )
                .first()
            )
            if not participation:
                return jsonify({"error": "Unauthorized"}), 403

        conversation.resolved = True  # type: ignore
        session.commit()

        return jsonify(
            {"status": "resolved", "message": "Conversation marked as resolved"}
        )


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
            select(Conversations.id, Conversations.title)
            .where(
                Conversations.initiated_by == user_email,
                Conversations.course_id == course_id,
            )
            .order_by(Conversations.id.desc())
        )
        result = session.execute(stmt).all()

    conversations = [{"id": row.id, "title": row.title} for row in result]
    return jsonify(conversations)


def generate_title(message: str):
    """Generates a title for a conversation on the sidebar

    :param message: the first message in a new conversation to be used to generate the title
    """
    prompt = f"With a user's first message in a AI chatbot conversation, {message}, generate a 30 character max title for this conversation. Do not actually answer the queestion, just sumarize it in 30 characters max. Do not generate anything else, only the 30 character max title"
    response = response_client.get_response(prompt)[0:30]

    return response


def create_conversation(course_id: int, user_email: str, message: str):
    """Initializes a new conversation in the database


    :param courseID: The id of the course
    :param user_email: The id of the user the conversations belongs to
    :param message: the first message within the new conversation
    """

    with Session(engine) as session:
        title = generate_title(message)

        new_conv = Conversations(
            course_id=course_id, initiated_by=user_email, title=title
        )
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

    return jsonify({"conversationId": conv_id, "title": title})


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
    with Session(engine) as session:
        # Check if conversation has been redirected to ULA
        conversation = (
            session.query(Conversations).filter_by(id=conversation_id).first()
        )
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404

        if bool(conversation.redirected) == True:
            return jsonify({"reply": ""})

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


def conversation_redirect_status(conversation_id: int):
    """Returns redirected status of a conversation based on the id.

    :param conversation_id: The ID of the current conversation.
    """
    with Session(engine) as session:
        course_id_row = (
            session.query(Conversations).filter_by(id=conversation_id).first()
        )

    if course_id_row is None:
        return jsonify({"redirect": False})

    if bool(course_id_row.redirected) == False and bool(
        course_id_row.resolved == False
    ):
        return jsonify({"redirect": "bot"})
    if bool(course_id_row.redirected) == True and bool(course_id_row.resolved) == False:
        return jsonify({"redirect": "open"})
    else:
        return jsonify({"redirect": "closed"})
