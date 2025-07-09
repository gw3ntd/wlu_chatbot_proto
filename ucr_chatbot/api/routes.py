from flask import Blueprint, request, jsonify
from .language_model import get_response_from_prompt, stream_response_from_prompt
from .context_retrieval import retriever

bp = Blueprint("routes", __name__)

SYSTEM_PROMPT = """# Main derective
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
    """Takes a JSON object with a prompt and responds with a JSON object containing a textual answer to the prompt."""

    kwargs: dict[str, str] = request.get_json()

    prompt = str(kwargs["prompt"])
    conversation_id = int(kwargs["conversation_id"])
    stream = bool(kwargs.get("stream", False))

    segments = retriever.get_segments_for(prompt, num_segments=3)

    context = "\n".join(
        map(lambda s: f"Reference number: {s.segment_id}, text: {s.text}", segments)
    )

    prompt_with_context = SYSTEM_PROMPT.format(context=context, question=prompt)

    if stream:
        return stream_response_from_prompt(prompt_with_context)
    else:
        return jsonify(
            {
                "text": get_response_from_prompt(prompt_with_context),
                "sources": [{"segment_id": 10}],
                "conversation_id": conversation_id,
            }
        )
