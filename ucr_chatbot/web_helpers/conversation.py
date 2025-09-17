from typing import cast, Optional
from flask import g
from flask_login import current_user  # type: ignore
from sqlalchemy.orm import Session
from pydantic import BaseModel as PydanticModel

from ucr_chatbot.db.models import (
    get_engine,
    Conversation,
    Message,
    MessageType,
    ConversationState,
)
from ucr_chatbot.api.language_model import LanguageModelClient
from ucr_chatbot.api.context_retrieval import retriever

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

CHARACTERS_PER_TOKEN = 4
MAX_TOKENS_PER_INTERACTION = 10_000
MAX_RESPONSE_TOKENS = 2000
MAX_CHARACTERS_PER_REQUEST = (
    MAX_TOKENS_PER_INTERACTION - MAX_RESPONSE_TOKENS
) * CHARACTERS_PER_TOKEN


def generate_response(
    client: LanguageModelClient,
    conversation_id: int,
    history: int = 5,
    max_tokens: int = MAX_RESPONSE_TOKENS,
    stop_sequences: list[str] | None = None,
) -> Optional["GenerationResponse"]:
    """Returns a bot message for a given conversation."""

    if stop_sequences is None:
        stop_sequences = []

    with Session(get_engine()) as session:
        conversation = session.get(Conversation, conversation_id)

        messages = (
            session.query(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.desc())
            .limit(history + 1)
        ).all()

    messages.reverse()

    if conversation is None:
        raise ValueError("conversation should not be None.")

    if len(messages) == 0 or messages[-1].type != MessageType.STUDENT_MESSAGE:  # type: ignore
        return None

    course_id: int = conversation.course_id  # type: ignore
    prompt = cast(str, messages[-1].body)

    segments = retriever.get_segments_for(prompt, course_id=course_id, num_segments=8)
    context = "\n".join(
        map(lambda s: f"Reference number: {s.id}, text: {s.text}", segments)
    )

    previous_messages = "\n".join(map(message_to_history, messages[:-1]))
    # request_character_count = len(context + prompt)

    # if request_character_count > MAX_CHARACTERS_PER_REQUEST:
    #     raise ValueError(f"Prompt and context are together too long: together they have {request_character_count} characters, but there must be fewer than {MAX_CHARACTERS_PER_REQUEST}")

    prompt_with_context = SYSTEM_PROMPT.format(
        context=context,
        question=prompt,
        history=previous_messages,  # [-MAX_CHARACTERS_PER_REQUEST + request_character_count:],
    )

    response_text = client.get_response(
        prompt=prompt_with_context, max_tokens=max_tokens
    )

    sources = [SegmentResponse(segment_id=s.id) for s in segments]

    return GenerationResponse(text=response_text, sources=sources)


class SegmentResponse(PydanticModel):
    segment_id: int


class GenerationResponse(PydanticModel):
    text: str
    sources: list[SegmentResponse]


def message_to_history(message: Message):
    """Converts a message to historical context for the language model."""
    sender = (
        "Student"
        if message.type == MessageType.STUDENT_MESSAGE  # type: ignore
        else (
            "Bot" if message.type == MessageType.BOT_MESSAGE else "Human Assistant"  # type: ignore
        )
    )

    return f"""### {sender}
{message.body}"""


def current_user_initiated_or_assists(conversation: Conversation):
    """Returns True iff a conversation was initiated by the current user or has
    been redirected to assistants and the current user is an assistant for the
    course.

    This assumes g.role is set, which should be done by @roles_required.
    """

    return (
        current_user.email == conversation.initiated_by
        or g.role == "assistant"
        and conversation.state
        in [ConversationState.REDIRECTED, ConversationState.RESOLVED]
    )
