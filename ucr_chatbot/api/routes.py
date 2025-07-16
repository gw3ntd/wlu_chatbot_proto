from flask import Blueprint, request, jsonify

# --- Import from your project's modules ---
from .context_retrieval import retriever
from .language_model.response import client
from ucr_chatbot.db.models import Session, engine, Messages, MessageType, Conversations
from sqlalchemy import select, insert

# A unique name for this blueprint
bp = Blueprint("api_routes", __name__)

# This should be replaced with a real, logged-in user in the future
USER_EMAIL_PLACEHOLDER = "test@ucr.edu"

SYSTEM_PROMPT = """# Main directive
You are a helpful student tutor for a university computer science course. You must assist students in their learning by answering question in a didactically useful way. You should only answer questions if you are certain that you know the correct answer.
You will be given context that may or may not be useful for answering the student's question followed by the question. Again, only answer the question if you are certain that you have a correct answer.

If the context is not relevant, than you should tell the student, "I cannot find any relevant course materials to help answer your question."

## Context
{context}

## Question
{question}
"""

# --- Consolidated API Routes ---


@bp.route("/conversation/<int:conversation_id>/messages", methods=["GET"])
def get_messages(conversation_id: int):
    """Gets the full message history for a given conversation.

    :param conversation_id: The ID of the conversation to retrieve.
    :return: A JSON response containing a list of message objects.
    """
    with Session(engine) as session:
        stmt = (
            select(Messages)
            .where(Messages.conversation_id == conversation_id)
            .order_by(Messages.timestamp.asc())
        )
        messages = session.execute(stmt).scalars().all()

        message_list = [
            {
                "id": msg.id,
                "body": msg.body,
                "sender": msg.type.name,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in messages
        ]
        return jsonify(message_list)


@bp.route("/conversation", methods=["POST"])
def create_conversation_and_get_reply():
    """Creates a new conversation and returns the bot's first RAG-powered reply.

    This endpoint expects a JSON body with the course ID and the user's
    initial prompt. It orchestrates creating the conversation, saving the
    user's message, generating a reply, and saving the bot's reply.

    :jsonparam course_id: The ID of the course for the new conversation.
    :jsonparam prompt: The user's first message text.
    :return: A JSON response with the new conversation_id, the bot's reply,
             and a list of sources, with a 201 status code.
    :raises 400: If the request body is not valid JSON or is missing keys.
    """
    content = request.json
    if not content or "course_id" not in content or "prompt" not in content:
        return jsonify(
            {"error": "Request body must contain 'course_id' and 'prompt'"}
        ), 400

    user_prompt = content["prompt"]

    with Session(engine) as session:
        # 1. Create the new conversation
        new_conv = Conversations(
            course_id=content["course_id"], initiated_by=USER_EMAIL_PLACEHOLDER
        )
        session.add(new_conv)
        session.commit()
        conversation_id = new_conv.id

        # 2. Save the user's first message
        session.execute(
            insert(Messages).values(
                body=user_prompt,
                conversation_id=conversation_id,
                type=MessageType.STUDENT_MESSAGES,
                written_by=USER_EMAIL_PLACEHOLDER,
            )
        )

        # 3. Get context and generate the bot's reply
        segments = retriever.get_segments_for(user_prompt, num_segments=3)
        context = "\n".join(s.text for s in segments)
        prompt_with_context = SYSTEM_PROMPT.format(
            context=context, question=user_prompt
        )
        bot_reply_text = client.get_response(prompt=prompt_with_context)

        # 4. Save the bot's reply
        session.execute(
            insert(Messages).values(
                body=bot_reply_text,
                conversation_id=conversation_id,
                type=MessageType.BOT_MESSAGES,
                written_by="bot",
            )
        )
        session.commit()

    return jsonify(
        {
            "conversation_id": conversation_id,
            "reply": bot_reply_text,
            "sources": [{"segment_id": s.id} for s in segments],  # type: ignore
        }
    ), 201


@bp.route("/conversation/<int:conversation_id>/message", methods=["POST"])
def send_message_and_get_reply(conversation_id: int):
    """Adds a user message to a conversation and returns the bot's RAG-powered reply.

    :param conversation_id: The ID of the conversation to add a message to.
    :jsonparam prompt: The user's new message text.
    :return: A JSON response with the bot's reply and a list of sources.
    :raises 400: If the request body is not valid JSON or is missing the prompt.
    """
    content = request.json
    if not content or "prompt" not in content:
        return jsonify({"error": "Request body must contain 'prompt'"}), 400

    user_prompt = content["prompt"]

    with Session(engine) as session:
        # 1. Save the user's new message
        session.execute(
            insert(Messages).values(
                body=user_prompt,
                conversation_id=conversation_id,
                type=MessageType.STUDENT_MESSAGES,
                written_by=USER_EMAIL_PLACEHOLDER,
            )
        )

        # 2. Get context and generate a new reply
        segments = retriever.get_segments_for(user_prompt, num_segments=3)
        context = "\n".join(s.text for s in segments)
        prompt_with_context = SYSTEM_PROMPT.format(
            context=context, question=user_prompt
        )
        bot_reply_text = client.get_response(prompt=prompt_with_context)

        # 3. Save the bot's new reply
        session.execute(
            insert(Messages).values(
                body=bot_reply_text,
                conversation_id=conversation_id,
                type=MessageType.BOT_MESSAGES,
                written_by="bot",
            )
        )
        session.commit()

    return jsonify(
        {
            "reply": bot_reply_text,
            "sources": [{"segment_id": s.id} for s in segments],  # type: ignore
        }
    )
