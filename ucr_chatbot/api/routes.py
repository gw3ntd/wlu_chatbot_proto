from flask import Blueprint, request, jsonify, Response
from .language_model import get_response_from_prompt, stream_response_from_prompt
from .context_retrieval import retriever
import json

bp = Blueprint("routes", __name__)

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
    conversation_id = params.get("conversation_id")
    stream = params.get("stream", False)

    # Get optional LLM parameters, with sensible defaults
    temperature = params.get("temperature", 0.4)
    max_tokens = params.get("max_tokens", 1024)

    if not prompt:
        return jsonify({"error": "Missing 'prompt' in request"}), 400

    # 2. Retrieve context from your context_retrieval module
    segments = retriever.get_segments_for(prompt, num_segments=3)
    context = "\n".join(
        # Assuming each 's' object has 'segment_id' and 'text' attributes
        map(lambda s: f"Reference number: {s.segment_id}, text: {s.text}", segments)
    )

    prompt_with_context = SYSTEM_PROMPT.format(context=context, question=prompt)

    # 3. Call the appropriate language model function with all parameters
    if stream:
        # Define a generator function to format the stream as Server-Sent Events (SSE)
        def stream_generator():
            for chunk in stream_response_from_prompt(
                prompt=prompt_with_context,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                # Format each chunk as a Server-Sent Event
                yield f"data: {json.dumps({'text': chunk})}\n\n"

        return Response(stream_generator(), mimetype="text/event-stream")
    else:
        response_text = get_response_from_prompt(
            prompt=prompt_with_context,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Dynamically create the list of source IDs
        sources = [{"segment_id": s.segment_id} for s in segments]
        
        return jsonify({
            "text": response_text,
            "sources": sources,
            "conversation_id": conversation_id,
        })