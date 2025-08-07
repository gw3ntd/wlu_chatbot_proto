from flask import (
    Blueprint,
    request,
    jsonify,
    Response,
)
from ucr_chatbot.db.models import Session, engine, Conversations
from .context_retrieval import retriever
from .language_model.response import client as client
import json
from ucr_chatbot.config import LLMMode

bp = Blueprint("routes", __name__)


SYSTEM_PROMPT = """# Main directive
You are a helpful student tutor for a university computer science course. You must assist students in their learning by answering question in a didactically useful way. You should only answer questions if you are certain that you know the correct answer.
You will be given context that may or may not be useful for answering the student's question followed by the question. Again, only answer the question if you are certain that you have a correct answer. The conversation history is also provided.

If the context is not relevant, then you should tell the student, "I cannot find any relevant course materials to help answer your question."

## Context
{context}

## History
{history}

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

    if (
        LLMMode.TESTING
    ):  # Single test with the generate route. No courses uploaded, so manually set it
        course_id = 0
    else:
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
        else:
            course_id = course_id_row.course_id

    # 2. Retrieve context from your context_retrieval module
    segments = retriever.get_segments_for(prompt, course_id, num_segments=3)  # type: ignore
    context = "\n".join(
        # Assuming each 's' object has 'segment_id' and 'text' attributes
        map(lambda s: f"Reference number: {s.id}, text: {s.text}", segments)  # type: ignore
    )

    prompt_with_context = SYSTEM_PROMPT.format(
        context=context, question=prompt, history="history"
    )

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
