from typing import Sequence


def embed_text(text: str) -> Sequence[float]:
    """Embeds text into a vector representation

    :param text: The text to be embeded.
    :return: The vector embedding for the text.
    """
    return [0.4, 0.2, 1.2, -1.1]
