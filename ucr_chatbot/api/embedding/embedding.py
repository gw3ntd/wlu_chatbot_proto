from typing import Sequence
import numpy as np
from ollama import Client

OLLAMA_URL = "localhost:11434"

client = Client(OLLAMA_URL)


def embed_text(text: str) -> Sequence[float]:
    """Embeds text into a vector representation

    :param text: The text to be embeded.
    :return: The vector embedding for the text.
    """
    global client

    numpy_array = np.array(
        client.embeddings("nomic-embed-text:latest", text).embedding, dtype=np.float64
    )
    embed: Sequence[float] = numpy_array.tolist()

    return embed
