from flask import (
    Blueprint,
    request,
    jsonify,
    Response,
    render_template,
    url_for,
    redirect,
)
from .context_retrieval import retriever
from .language_model.response import client as client
import json
from ucr_chatbot.db.models import Session, engine, Messages, MessageType, Conversations
from sqlalchemy import select, insert

bp = Blueprint("routes", __name__)


@bp.route("/")
def course_selection():
    """Responds with a landing page where a student can select a course"""
    return render_template(
        "landing_page.html",
        title="Landing Page",
        body=f'Select your course. <a href="{url_for(".new_conversation", course_id="1")}"> CS009A </a>',
    )


@bp.route("/course/<int:course_id>/chat")
def new_conversation(course_id: int):
    """Redirects to a page with a new conversation for a course.
    :param course_id: The id of the course for which a conversation will be initialized.
    """
    return redirect(url_for(".conversation", conversation_id=course_id))


# @bp.route("/conversations/<int:conversation_id>")
# def conversation(conversation_id: int):
#     """Responds with page where a student can interact with a chatbot for a course.

#     :param conversation_id: The id of the conversation to be send back to the user.
#     """
#     with Session(engine) as session:
#         stmt = (
#             select(Messages)
#             .where(Messages.conversation_id == conversation_id)
#             .order_by(Messages.timestamp.asc())
#         )
#         messages = session.execute(stmt).scalars().all()

#         type_map = {
#             MessageType.STUDENT_MESSAGES: "StudentMessage",
#             MessageType.BOT_MESSAGES: "BotMessage",
#         }
#         messages_list = []
#         for message in messages:
#             sender = type_map.get(message.type)  # type: ignore
#             message_dict = {
#                 "id": message.id,
#                 "body": message.body,
#                 "sender": sender,
#                 "timestamp": message.timestamp.isoformat(),
#             }
#             messages_list.append(message_dict)  # type: ignore

#         return jsonify({"messages": messages_list})
    
@bp.route("/conversations/<int:conversation_id>")
def conversation(conversation_id: int):
    """Responds with page where a student can interact with a chatbot for a course.

    :param conversation_id: The id of the conversation to be send back to the user.
    """
    with Session(engine) as session:
        stmt = (
            select(Messages)
            .where(Messages.conversation_id == conversation_id)
            .order_by(Messages.timestamp.asc())
        )
        messages = session.execute(stmt).scalars().all()

    return render_template(
        "conversation.html",  
        conversation_id=conversation_id,
        messages=messages 
    )



user_email = "test@ucr.edu"


@bp.route("/create_conversation", methods=["POST"])
def create_conversation():
    """Responds with a landing page where a student can select a course"""

    content = request.json
    if not content:
        return jsonify({"error": "Request body must be valid JSON"}), 400
    print(content["courseId"])
    print(content["message"])
    with Session(engine) as session:
        new_conv = Conversations(course_id=content["courseId"], initiated_by=user_email)
        session.add(new_conv)
        session.commit()

        conv_id = new_conv.id

        insert_msg = insert(Messages).values(
            body=content["message"],
            conversation_id=conv_id,
            type=MessageType.STUDENT_MESSAGES,
            written_by=user_email,
        )
        session.execute(insert_msg)
        session.commit()
    return {"conversationId": conv_id}


@bp.route("/conversations/<int:conversation_id>/reply", methods=["POST"])
def reply_conversation(conversation_id: int):
    """Saves a placeholder bot reply to the database.

    :param conversation_id: The ID of the current conversation.
    """
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

    return {"reply": llm_response}


@bp.route("/conversations/<int:conversation_id>/send", methods=["POST"])
def send_message(conversation_id: int):
    """Saves a new user message to the database.

    :param conversation_id: The ID of the current conversation.
    """
    content = request.json
    if not content:
        return jsonify({"error": "Request body must be valid JSON"}), 400
    print("Input message: " + str(content["message"]))
    with Session(engine) as session:
        insert_msg = insert(Messages).values(
            body=content["message"],
            conversation_id=conversation_id,
            type=MessageType.STUDENT_MESSAGES,
            written_by=user_email,
        )
        session.execute(insert_msg)
        session.commit()

    return {"status": "200"}


@bp.route("/conversations/get_conversations", methods=["POST"])
def get_conversations():
    """Gets all conversation IDs for the test user."""
    data = request.get_json()
    course_id = data.get("courseId")

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


@bp.route("/course/<int:course_id>/documents")
def course_documents(course_id: int):
    """Responds with a page where a course administrator can add more documents
    to the course for use by the retrieval-augmented generation system.
    :param course_id: The id of the course for which a conversation will be initialized.
    """
    return render_template(
        "base.html",
        title="Landing Page",
        body=f"These are the documents for the course with id {course_id}",
    )


SYSTEM_PROMPT = """# Main directive
You are a helpful student tutor for a university computer science course. You must assist students in their learning by answering question in a didactically useful way. You should only answer questions if you are certain that you know the correct answer.
You will be given context that may or may not be useful for answering the student's question followed by the question. Again, only answer the question if you are certain that you have a correct answer.

If the context is not relevant, than you should tell the student, "I cannot find any relevant course materials to help answer your question."

## Context
{context}

## Question
{question}
"""


@bp.route("/generate", methods=["POST"])
def generate():
    """
    Takes a JSON object with a prompt and other parameters,
    and responds with a JSON object or a stream.
    """
    # 1. Get all parameters from the incoming JSON request
    params = request.get_json()
    if not params:
        return jsonify({"error": "Invalid JSON"}), 400
    prompt = params.get("prompt")
    if not prompt:
        return jsonify({"error": "Missing 'prompt' in request"}), 400

    conversation_id = params.get("conversation_id")
    stream = params.get("stream", False)
    temperature = params.get("temperature", 1.0)
    max_tokens = params.get("max_tokens", 3000)
    stop_sequences = params.get("stop_sequences", [])

    # 2. Retrieve context from your context_retrieval module
    segments = retriever.get_segments_for(prompt, num_segments=3)
    context = "\n".join(
        # Assuming each 's' object has 'segment_id' and 'text' attributes
        map(lambda s: f"Reference number: {s.id}, text: {s.text}", segments)  # type: ignore
    )

    prompt_with_context = SYSTEM_PROMPT.format(context=context, question=prompt)

    generation_params = {
        "prompt": prompt_with_context,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stop_sequences": stop_sequences,
    }

    # 3. Call the appropriate language model function with all parameters
    if stream:
        # Define a generator function to format the stream as Server-Sent Events (SSE)
        def stream_generator():
            for chunk in client.stream_response(**generation_params):  # type: ignore
                # Format each chunk as a Server-Sent Event
                yield f"data: {json.dumps({'text': chunk})}\n\n"

        return Response(stream_generator(), mimetype="text/event-stream")
    else:
        response_text = client.get_response(**generation_params)  # type: ignore

        # Dynamically create the list of source IDs
        sources = [{"segment_id": s.id} for s in segments]  # type: ignore

        return jsonify(
            {
                "text": response_text,
                "sources": sources,
                "conversation_id": conversation_id,
            }
        )
