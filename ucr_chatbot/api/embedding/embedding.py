from typing import Sequence
from ollama import Client

OLLAMA_URL = "localhost:11434"

client = Client(OLLAMA_URL)


def embed_text(text: str) -> Sequence[float]:
    """Embeds a string of text into a vector representation.

    :param text: The text to be embedded.
    :return: A list of floats representing the vector embedding.
    """
    global client

    embedding = client.embeddings("nomic-embed-text:latest", text).embedding
    embed: Sequence[float] = list(embedding) if not isinstance(embedding, list) else embedding

    return embed
