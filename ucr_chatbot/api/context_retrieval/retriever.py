from sqlalchemy.orm import Session
from typing import List
from dataclasses import dataclass

from ucr_chatbot.db.models import get_engine, Segment, Embedding, Document

from ..embedding.embedding import embed_text


@dataclass
class RetrievedSegment:
    """A dataclass to hold the retrieved segment's data."""

    id: int
    text: str
    document_name: str


class Retriever:
    """
    Retrieves relevant text segments from the database using vector search.
    """

    def get_segments_for(
        self,
        prompt: str,
        course_id: int,
        num_segments: int = 3,
    ) -> List[RetrievedSegment]:
        """
        Gets relevant segments from the database by performing a vector similarity search.

        :param prompt: The user's prompt for which to find context.
        :param num_segments: The number of segments to retrieve.
        :return: A list of RetrievedSegment objects.
        """
        prompt_embedding = embed_text(prompt)

        with Session(get_engine()) as session:
            results = (
                session.query(Segment, Document.name)
                .join(Embedding)
                .join(Document)
                .filter(Document.course_id == course_id)
                .order_by(Embedding.vector.l2_distance(prompt_embedding))
                .limit(num_segments)
                .all()
            )

            retrieved_segments = [
                RetrievedSegment(
                    id=segment.id,  # type: ignore
                    text=segment.text,  # type: ignore
                    document_name=name,  # type: ignore
                )
                for segment, name in results
            ]

        return retrieved_segments


retriever = Retriever()
