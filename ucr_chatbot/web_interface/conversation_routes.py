from typing import Any, cast


from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    abort,
)
from flask_login import current_user, login_required  # type: ignore
from pydantic import BaseModel as PydanticModel

from ucr_chatbot.api.language_model.response import LanguageModelClient
from ucr_chatbot.decorators import roles_required, consent_required
from ucr_chatbot.web_helpers.limit import (
    get_language_model_client_with_limit_info,
    LimitUsageList,
    TOO_MANY_REQUESTS,
)
from ucr_chatbot.web_helpers.conversation import (
    current_user_initiated_or_assists,
    generate_response,
    SegmentResponse,
)
from ucr_chatbot.db.models import (
    Session,
    get_engine,
    ConversationState,
    Conversation,
    ParticipatesIn,
    Message,
    MessageType,
    Reference,
)


bp = Blueprint("conversation_routes", __name__)


def get_course_from_url(kwargs: dict[str, Any]):
    """Gets the course id from the url"""
    return int(kwargs["course_id"])


def get_course_from_query_parameter(_: dict[str, Any] = {}):
    """Gets the course id from a query parameter"""
    course_id = request.args.get("course_id", None)
    if course_id is None:
        return None
    return int(course_id)


def get_course_from_json_body(_: dict[str, Any]):
    """"""
    return request.json and int(request.json["course_id"])


def get_course_from_conversation_in_url(kwargs: dict[str, Any]):
    """Gets the course id from the conversation_id in the url."""
    with Session(get_engine()) as session:
        conversation = session.get(Conversation, int(kwargs["conversation_id"]))
        if conversation is None:
            return None
        return int(conversation.course_id)  # type: ignore


@bp.get("/conversations/new/")
@login_required
@roles_required(["student", "assistant", "instructor"], get_course_from_query_parameter)
@consent_required(get_course_from_query_parameter)
def new_conversation():
    """Renders the conversation page for a new conversation.

    :param course_id: The id of the course for which a conversation will be initialized.
    """

    course_id = get_course_from_query_parameter()

    with Session(get_engine()) as session:
        number_of_assistants = (
            session.query(ParticipatesIn)
            .where(ParticipatesIn.role == "assistant")
            .count()
        )

    return render_template(
        "conversation.html",
        course_id=course_id,
        conversation_state="CHATBOT",
        redirectable=number_of_assistants > 0,
    )


@bp.post("/conversations")
@login_required
@roles_required(["student", "assistant", "instructor"], get_course_from_json_body)
@consent_required(get_course_from_json_body)
def post_conversation():
    """Creates a new conversation."""
    data = PostConversationRequest.model_validate(request.json)

    limit_usages = LimitUsageList.get(current_user.email, data.course_id)

    if limit_usages.reached:
        return jsonify(
            LimitReachedResponse(
                error="Could not create a new conversation because one of your rate limits has been violated for this course: Wait until you have available usages before submitting another request."
            ).model_dump()
        ), TOO_MANY_REQUESTS

    with Session(get_engine()) as session:
        new_conv = Conversation(
            course_id=data.course_id, initiated_by=current_user.email, title=data.title
        )
        session.add(new_conv)
        session.commit()

        conv_id = cast(int, new_conv.id)

    return jsonify(PostConversationResponse(conversation_id=conv_id).model_dump())


@bp.get("/conversations")
@login_required
@roles_required(["student", "assistant", "instructor"], get_course_from_query_parameter)
@consent_required(get_course_from_query_parameter)
def get_conversations():
    """Responds with all conversations in JSON form."""
    course_id = get_course_from_query_parameter()
    with Session(get_engine()) as session:
        conversations = (
            session.query(Conversation)
            .where(
                Conversation.initiated_by == current_user.email,
                Conversation.course_id == course_id,
            )
            .order_by(Conversation.id.desc())
            .all()
        )

    conversations = [
        ConversationResponse(id=conv.id, title=conv.title, state=conv.state)  # type: ignore
        for conv in conversations
    ]
    return jsonify(ConversationListResponse(conversations=conversations).model_dump())


@bp.get("/conversations/<int:conversation_id>")
@login_required
@roles_required(
    ["student", "assistant", "instructor"], get_course_from_conversation_in_url
)
def get_conversation(conversation_id: int):
    """Respnds with either a JSON or HTML representation of a conversation."""
    with Session(get_engine()) as session:
        conv = session.get(Conversation, conversation_id)
        if conv is None:
            abort(404)

        if not current_user_initiated_or_assists(conv):
            abort(403)

        course_id = conv.course_id

        if (
            request.accept_mimetypes.accept_json
            and not request.accept_mimetypes.accept_html
        ):
            return jsonify(
                ConversationResponse(
                    id=conversation_id,  # type: ignore
                    title=conv.title,  # type: ignore
                    state=str(conv.state).split(".")[-1],
                ).model_dump()
            )

        number_of_assistants = (
            session.query(ParticipatesIn)
            .where(ParticipatesIn.role == "assistant")
            .count()
        )

    conversation_state = str(conv.state).split(".")[-1]

    return render_template(
        "conversation.html",
        conversation_id=conversation_id,
        course_id=course_id,
        conversation_state=conversation_state,
        redirectable=number_of_assistants > 0,
    )


@bp.patch("/conversations/<int:conversation_id>")
@login_required
@roles_required(
    ["student", "assistant", "instructor"], get_course_from_conversation_in_url
)
def patch_conversation(conversation_id: int):
    """Updates a conversation."""
    data = PatchConversationRequest.model_validate(request.json)
    with Session(get_engine()) as session:
        conversation = session.get(Conversation, conversation_id)
        if conversation is None:
            abort(404)
        if data.state is not None:
            if not current_user_initiated_or_assists(conversation):
                abort(403)
            match (conversation.state, data.state):
                case (ConversationState.CHATBOT, ConversationState.REDIRECTED):
                    number_of_assistants = (
                        session.query(ParticipatesIn)
                        .where(ParticipatesIn.role == "assistant")
                        .count()
                    )
                    if number_of_assistants == 0:
                        abort(400)
                    conversation.state = ConversationState.REDIRECTED
                case (ConversationState.REDIRECTED, ConversationState.RESOLVED):
                    conversation.state = ConversationState.RESOLVED
                case _:
                    abort(400)
        session.commit()

    return "", 204


@bp.post("/conversations/<int:conversation_id>/ai-responses")
@login_required
@roles_required(
    ["student", "assistant", "instructor"], get_course_from_conversation_in_url
)
def post_ai_response(conversation_id: int):
    """Generates a new ai generated Message for a conversation that responds to the historical context of the conversation."""
    with Session(get_engine()) as session:
        conv = session.get(Conversation, conversation_id)
        if conv is None:
            abort(404)
        if conv.initiated_by != current_user.email:
            abort(403)
        client, limit_usages = get_language_model_client_with_limit_info(
            current_user.email,
            conv.course_id,  # type: ignore
        )

        if limit_usages.reached:
            return jsonify(
                LimitReachedResponse(
                    error="Could not generate a response from from the AI Tutor because one of your rate limits has been violated for this course: Wait until you have available usages before submitting another request."
                ).model_dump()
            ), TOO_MANY_REQUESTS

        number_of_messages = (
            session.query(Message)
            .where(Message.conversation_id == conversation_id)
            .count()
        )

        if number_of_messages == 0:
            abort(
                400,
                "There must be at least one message in the conversation before the AI Tutor can responsd.",
            )
        elif number_of_messages == 1:
            first_message = (
                session.query(Message)
                .where(Message.conversation_id == conversation_id)
                .one()
            )
            title = generate_title(client, cast(str, first_message.body))
            conv.title = title  # type: ignore
            session.commit()

        conversation_title = str(conv.title)

    response = generate_response(client, conversation_id=conversation_id)
    if response is None:
        # This would likely be because the most recent message in the chat
        # was not a student message.
        abort(400, "Could not generate an AI Tutor response.")

    with Session(get_engine()) as session:
        bot_message = Message(
            body=response.text,
            type=MessageType.BOT_MESSAGE,
            written_by=current_user.email,
            conversation_id=conversation_id,
        )
        session.add(bot_message)

        session.commit()

        for source in response.sources:
            session.add(
                Reference(message_id=bot_message.id, segment_id=source.segment_id)
            )

        session.commit()
        return jsonify(
            PostAiResponse(
                text=response.text, title=conversation_title, sources=response.sources
            ).model_dump()
        )


def generate_title(client: LanguageModelClient, message: str):
    """Generates a title for a conversation on the sidebar.
    Only uses the beginning of the prompt to ensure that this generation is not too computationally expensive.

    :param message: the first message in a new conversation to be used to generate the title
    """
    prompt = f"With a user's first message in a AI chatbot conversation, {message}, generate a 30 character max title for this conversation. Do not actually answer the queestion, just sumarize it in 30 characters max. Do not generate anything else, only the 30 character max title"
    response = client.get_response(
        [{"role": "user", "parts": [{"text": prompt}]}], max_tokens=30
    )

    return response.get_text()[:30]


class ConversationResponse(PydanticModel):
    id: int
    title: str
    state: str


class ConversationListResponse(PydanticModel):
    conversations: list[ConversationResponse]


class PostAiResponse(PydanticModel):
    text: str
    title: str
    sources: list[SegmentResponse]


class PostConversationRequest(PydanticModel):
    course_id: int
    title: str


class PostConversationResponse(PydanticModel):
    conversation_id: int


class PatchConversationRequest(PydanticModel):
    state: ConversationState | None


class LimitReachedResponse(PydanticModel):
    error: str
