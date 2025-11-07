from typing import cast
import datetime

from sqlalchemy.orm import Session
from pydantic import BaseModel as PydanticModel

from wlu_chatbot.api.language_model import (
    LanguageModelClient,
    get_language_model_client,
)
from wlu_chatbot.db.models import (
    get_engine,
    Limit,
    Conversation,
    Message,
    MessageType,
)


class LimitUsage(PydanticModel):
    """Contains information about a limmit and whether it has been reached"""

    uses: int
    time_span_seconds: int
    maximum_number_of_uses: int
    limit_id: int

    @property
    def reached(self) -> bool:
        """Returns True iff the limit has been reached"""
        return self.uses >= self.maximum_number_of_uses


class LimitUsageList(list[LimitUsage]):
    """A list of LimitUsage"""

    @property
    def reached(self):
        """True iff at least one of the contained limits is reached."""
        reached = False
        for limit in self:
            reached |= limit.reached
        return reached

    @staticmethod
    def get(email: str, course_id: int):
        """Gets the limit usages for a user in a course."""

        # TODO: Consider whether conversation creation, which uses the LLM to generate a title,
        # leads to enough LLM usage to warrant working toward the usage limit.

        limit_usages: LimitUsageList = LimitUsageList()
        with Session(get_engine()) as sess:
            limits = sess.query(Limit).where(Limit.course_id == course_id).all()
            conversation_ids = [
                c[0]
                for c in (
                    sess.query(Conversation.id)
                    .where(
                        Conversation.initiated_by == email,
                        Conversation.course_id == course_id,
                    )
                    .all()
                )
            ]
            for limit in limits:
                beginning_of_span = datetime.datetime.now(
                    datetime.timezone.utc
                ) - datetime.timedelta(
                    seconds=limit.time_span_seconds  # type: ignore
                )

                bot_messages = sess.query(Message).where(
                    (Message.conversation_id.in_(conversation_ids))
                    & (Message.type == MessageType.BOT_MESSAGE)
                    & (Message.timestamp > beginning_of_span)
                )

                limit_usages.append(
                    LimitUsage(
                        uses=bot_messages.count(),
                        time_span_seconds=limit.time_span_seconds,  # type: ignore
                        maximum_number_of_uses=limit.maximum_number_of_uses,  # type: ignore
                        limit_id=cast(int, limit.id),
                    )
                )

        return limit_usages


def get_language_model_client_with_limit_info(
    email: str, course_id: int
) -> tuple[LanguageModelClient, LimitUsageList]:
    """Returns the language model client along with the current user's limit."""

    client = get_language_model_client()

    limit_usages = LimitUsageList.get(email, course_id)

    return (client, limit_usages)


TOO_MANY_REQUESTS = 429
