from typing import List
from .document import Segment


class Retriever:
    """Allows for the retrieval of textual information."""

    def get_segments_for(self, prompt: str, num_segments: int = 1) -> List[Segment]:
        """Gets relevant Segments that could be relevant to a prompt.

        :param prompt: The prompt for which context segments are found.
        :param num_segments: The number of context segments to be found.
            Defaults to 1.
        :return: The Segments that contain informataion relevant to the prompt.
        """
        return [
            Segment(f'Context {i} for "{prompt}".', i, 1) for i in range(num_segments)
        ]
