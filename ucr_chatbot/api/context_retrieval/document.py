from typing import Iterable


class Document:
    """Represents a single document."""

    def __init__(self, name: str, document_id: int):
        """Initializes a Document with a name and document_id."""
        self._name = name
        self._document_id = document_id

    @property
    def name(self) -> str:
        """The name of this Document."""
        return self._name

    @property
    def document_id(self) -> int:
        """The id of this Document."""
        return self._document_id

    def get_segments(self) -> Iterable["Segment"]:
        """An iterable over all segments for this Document in order."""
        raise NotImplementedError()

    def __iter__(self) -> Iterable["Segment"]:
        """Iterates over all segments for this Document in order."""
        return self.get_segments()


class Segment:
    """Represents a single segment of text from a document."""

    def __init__(self, text: str, segment_id: int, document_id: int):
        """Initializes a segment with text, an id for the segment, and an id for the document that contains the segment."""
        self._text = text
        self._segment_id = segment_id
        self._document_id = document_id

    @property
    def text(self) -> str:
        """The text for this segment."""
        return self._text

    @property
    def segment_id(self) -> int:
        """The id of this segment."""
        return self._segment_id

    @property
    def document_id(self) -> int:
        """The id of the document containing this segment."""
        return self._document_id
