from typing import Any, cast


from flask import (
    Blueprint,
    request,
    jsonify,
    abort,
    g,
)
from flask_login import current_user, login_required  # type: ignore
from pydantic import BaseModel as PydanticModel

from ucr_chatbot.decorators import roles_required, consent_required
from ucr_chatbot.web_helpers.limit import LimitUsageList, TOO_MANY_REQUESTS
from ucr_chatbot.db.models import (
    Session,
    get_engine,
    Message,
    MessageType,
    ConversationState,
    Conversation,
    Segment,
    Document,
    Reference,
)


bp = Blueprint("message_routes", __name__)


def get_course_from_conversation_in_query_parameter(_: dict[str, Any] = {}):
    """"""
    conversation_id = request.args.get("conversation_id")
    if conversation_id is None:
        return None

    with Session(get_engine()) as session:
        course_id = (
            session.query(Conversation.course_id)
            .where(Conversation.id == conversation_id)
            .scalar()
        )
        return int(course_id)


def get_course_from_conversation_in_json_body(_: dict[str, Any] = {}):
    """"""
    data = request.json
    if data is None:
        return None

    conversation_id = int(data["conversation_id"])

    with Session(get_engine()) as session:
        course_id = (
            session.query(Conversation.course_id)
            .where(Conversation.id == conversation_id)
            .scalar()
        )
        return int(course_id)


def get_course_from_message_in_url(kwargs: dict[str, Any]):
    """"""

    message_id = int(kwargs["message_id"])
    with Session(get_engine()) as session:
        course_id = (
            session.query(Conversation.course_id)
            .join(Message, Conversation.id == Message.conversation_id)
            .where(Message.id == message_id)
            .scalar()
        )

    return course_id


@bp.get("/messages")
@login_required
@roles_required(
    ["student", "assistant", "instructor"],
    get_course_from_conversation_in_query_parameter,
)
@consent_required(get_course_from_conversation_in_query_parameter)
def get_messages():
    """Responds with the messages for a conversation."""
    data = MessageListRequest.model_validate(request.args.to_dict())

    with Session(get_engine()) as session:
        conv = session.get(Conversation, data.conversation_id)
        if conv is None:
            abort(404)

        if not (
            conv.initiated_by == current_user.email
            or g.role == "assistant"
            and conv.state in [ConversationState.REDIRECTED, ConversationState.RESOLVED]
        ):
            abort(403)

        messages = (
            session.query(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.timestamp.asc())
        ).all()

    return jsonify(
        MessageListResponse(
            messages=[
                MessageResponse(
                    type=MessageType(m.type),
                    body=str(m.body),
                    message_id=cast(int, m.id),
                )
                for m in messages
            ]
        ).model_dump()
    )


@bp.post("/messages")
@login_required
@roles_required(
    ["student", "assistant", "instructor"],
    get_course_from_conversation_in_json_body,
)
@consent_required(get_course_from_conversation_in_json_body)
def post_message():
    """Creates a new message in a conversation."""
    data = PostMessageRequest.model_validate(request.json)

    with Session(get_engine()) as session:
        conv = session.get(Conversation, data.conversation_id)
        if conv is None:
            abort(404)
        if not (
            conv.state in [ConversationState.CHATBOT, ConversationState.REDIRECTED]
        ):
            abort(403)
        if not (
            conv.initiated_by == current_user.email
            or (g.role == "assistant" and conv.state in [ConversationState.REDIRECTED])
        ):
            abort(403)
        if (
            conv.state == ConversationState.CHATBOT
            and LimitUsageList.get(
                current_user.email, cast(int, conv.course_id)
            ).reached
        ):
            abort(
                TOO_MANY_REQUESTS,
                "Could not send message because one of your rate limits for this course has been reached. Please wait until you have some usages before sending another request.",
            )
        message = Message(
            conversation_id=conv.id,
            body=data.body,
            written_by=current_user.email,
            type=MessageType.ASSISTANT_MESSAGE
            if g.role == "assistant"
            else MessageType.STUDENT_MESSAGE,
        )

        session.add(message)
        session.commit()

        if not (
            conv.initiated_by == current_user.email
            or g.role == "assistant"
            and conv.state in [ConversationState.REDIRECTED, ConversationState.RESOLVED]
        ):
            abort(403)

    return ""


@bp.get("/messages/<int:message_id>/sources")
@login_required
@roles_required(
    ["student", "assistant", "instructor"],
    get_course_from_message_in_url,
)
@consent_required(get_course_from_message_in_url)
def get_message_sources(message_id: int):
    """Responds with the sources referenced by a message."""

    with Session(get_engine()) as session:
        message = session.get(Message, message_id)
        if not message:
            abort(404)
        if message.written_by != current_user.email:
            abort(403)

        source_results = cast(
            list[tuple[str, str]],
            session.query(Segment.text, Document.name)
            .join(Reference, Segment.id == Reference.segment_id)
            .join(Document, Segment.document_id == Document.id)
            .where(Reference.message_id == message_id)
            .all(),
        )

        sources = [
            Source(text=segment_text, document_name=document_name)
            for segment_text, document_name in source_results
        ]

    return jsonify(GetMessageSourcesResponse(sources=sources).model_dump())


class Source(PydanticModel):
    document_name: str
    text: str


class GetMessageSourcesResponse(PydanticModel):
    sources: list[Source]


class PostMessageRequest(PydanticModel):
    conversation_id: int
    body: str


class MessageListRequest(PydanticModel):
    conversation_id: int


class MessageResponse(PydanticModel):
    type: MessageType
    body: str
    message_id: int


class MessageListResponse(PydanticModel):
    messages: list[MessageResponse]
