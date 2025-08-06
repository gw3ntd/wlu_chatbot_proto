from sqlalchemy.orm import Session
from typing import List
from dataclasses import dataclass

# --- Import from your other project files ---
# Import the engine and table classes from your database file
from ...db.models import engine, Segments, Embeddings, Documents

# Import your embedding function
from ..embedding.embedding import embed_text

# --- Data Structure for a Segment ---


@dataclass
class RetrievedSegment:
    """A dataclass to hold the retrieved segment's data."""

    id: int
    text: str
    document_id: str


# --- Retriever Implementation ---


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
        # 1. Embed the user's prompt into a vector.
        prompt_embedding = embed_text(prompt)

        # 2. Use a SQLAlchemy session to query the database.
        with Session(engine) as session:
            # 3. Build the query using the ORM.
            # This query joins Segments and Embeddings, orders the results by how
            # close their vectors are to the prompt's vector, and takes the top results.
            results = (
                session.query(Segments)
                .join(Embeddings)
                .join(Documents)
                .filter(Documents.course_id == course_id)
                .order_by(Embeddings.vector.l2_distance(prompt_embedding))
                .limit(num_segments)
                .all()
            )

            # 4. Format the SQLAlchemy objects into simple data objects.
            retrieved_segments = [
                RetrievedSegment(
                    id=segment.id,  # type: ignore
                    text=segment.text,  # type: ignore
                    document_id=segment.document_id,  # type: ignore
                )
                for segment in results
            ]

        return retrieved_segments


# Create a single, global instance for the rest of the app to use
retriever = Retriever()
