from flask import (
    Blueprint,
)

from sqlalchemy import select, func

from datetime import datetime
from ucr_chatbot.api.language_model.response import client as response_client
from typing import List, Optional


from ucr_chatbot.db.models import (
    Session,
    engine,
    Messages,
    Conversations,
    MessageType,
)


bp = Blueprint("web_routes", __name__)


def generate_conversation_summary(
    conversation_id: int,
    prompt: str,
    time_start: Optional[datetime],
    time_end: Optional[datetime],
) -> str:
    """Generates a summary from a given prompt of all student-chatbot interactions that occurred in a single conversation between a start and end time."""
    with Session(engine) as session:
        total_messages: List[str] = []

        stmt = (
            select(Messages.type, Messages.body)
            .join(Conversations, Messages.conversation_id == Conversations.id)
            .where(Conversations.id == conversation_id)
        )
        if time_start:
            stmt = stmt.where(Messages.timestamp > time_start)
        if time_end:
            stmt = stmt.where(Messages.timestamp < time_end)

        stmt = stmt.order_by(Messages.timestamp)

        messages = session.execute(stmt).all()

        type_map = {
            MessageType.STUDENT_MESSAGES: "StudentMessage",
            MessageType.BOT_MESSAGES: "BotMessage",
            MessageType.ASSISTANT_MESSAGES: "AssistantMessage",
        }

        for message in messages:
            total_messages.append(f"{type_map.get(message.type)}: {message.body}")

        total_messages_txt = "\n".join(total_messages)

        prompt = prompt + total_messages_txt
        response = response_client.get_response(prompt)

        return response


def generate_usage_summary(
    course_id: int,
    time_start: Optional[datetime],
    time_end: Optional[datetime],
    course_name: str,
) -> str:
    """Generates a summary of all student-chatbot interactions that occurred between a start and end time."""

    with Session(engine) as session:
        stmt = (
            select(func.count(func.distinct(Messages.written_by)))
            .join(Conversations, Messages.conversation_id == Conversations.id)
            .where(Conversations.course_id == course_id)
        )

        if time_start:
            stmt = stmt.where(Messages.timestamp > time_start)
        if time_end:
            stmt = stmt.where(Messages.timestamp < time_end)

        student_count = session.execute(stmt).scalar_one()

        stmt = (
            select(func.count(func.distinct(Messages.conversation_id)))
            .join(Conversations, Messages.conversation_id == Conversations.id)
            .where(Conversations.course_id == course_id)
        )

        if time_start:
            stmt = stmt.where(Messages.timestamp > time_start)
        if time_end:
            stmt = stmt.where(Messages.timestamp < time_end)

        conv_count = session.execute(stmt).scalar_one()

        stmt = (
            select(func.distinct(Messages.conversation_id))
            .join(Conversations, Messages.conversation_id == Conversations.id)
            .where(Conversations.course_id == course_id)
        )
        if time_start:
            stmt = stmt.where(Messages.timestamp > time_start)
        if time_end:
            stmt = stmt.where(Messages.timestamp < time_end)

        conversation_ids = session.execute(stmt).scalars().all()

        total_messages: List[str] = []
        prompt = """These are all of the messages within one conversation between a student and a AI chatbot tutor. Create a summary of this conversation, including topics discussed and student performance.
        Also include a section for specific topics being discussed where students talked to a human assistant. Messages labeled 'AssistantMessage' represent human assistants"""
        for conv_id in conversation_ids:
            total_messages.append(
                generate_conversation_summary(conv_id, prompt, time_start, time_end)
            )

        total_messages_txt = "\n".join(total_messages)

    prompt = f"""These are all of the messages that students have been having with a AI chatbot for help with a computer science course. 
                Generate a report for this course's instructor summarising students\' interactions with the chatbot, highlighting common questions and students\' strengths and weaknesses
                Here are the all student chatbot messages {total_messages_txt}
                Do not include any information of chatbot performance, or include recommendations for the professor
                Do not focus too much on specific/invidual interactions between a student and the chatbot. 
                Focus more higher level, what topics are being discussed and with what frequency, which topics are students struggling at, how are they struggling.
                Do not include a title for the report.
                Also include a section for specific topics where students needed help and required talking to a human assistant.
                """

    response = response_client.get_response(prompt)

    if time_start and time_end:
        title = f"## {course_name} Chatbot Interaction Report ({time_start.date()} - {time_end.date()})\n\n"
    elif time_start:
        title = f"## {course_name} Chatbot Interaction Report ({time_start.date()} - Present)\n\n"
    else:
        title = f"## {course_name} Chatbot Interaction Report\n\n"

    summary = (
        title
        + "Active Students: "
        + str(student_count)
        + "\nTotal Conversations: "
        + str(conv_count)
        + "\n\n"
        + response
    )

    return summary
