from typing import Sequence
from ollama import Client
from ucr_chatbot.config import app_config, LLMMode
from flask import g


def get_embedding_client() -> Client | None:
    """Gets the Ollama client instance. Must be called from within an request context."""
    if g.get("_embedding_client") is None:
        match app_config.LLM_MODE:
            case LLMMode.TESTING:
                return None
            case _:
                g._embedding_client = Client(host=app_config.OLLAMA_URL)
                return g._embedding_client
    return g._embedding_client


def embed_text(text: str) -> Sequence[float]:
    """Embeds a string of text into a vector representation.
    Must be called from within a request context.

    :param text: The text to be embedded.
    :return: A list of floats representing the vector embedding.
    """

    client = get_embedding_client()
    if client is None:
        return [0.1, 0.2, 0.3, 0.4, 0.5] * 20

    response = client.embeddings(model="nomic-embed-text", prompt=text)  # type: ignore
    embedding = response["embedding"]
    embed = list(embedding)

    return embed
