from typing import Sequence
from ollama import Client
from ucr_chatbot.config import Config, LLMMode

if Config.LLM_MODE == LLMMode.TESTING:
    client = None
else:
    try:
        client = Client(host=Config.OLLAMA_URL)
    except Exception as e:
        raise ConnectionError(
            f"Could not connect to Ollama at {Config.OLLAMA_URL}"
        ) from e


def embed_text(text: str) -> Sequence[float]:
    """Embeds a string of text into a vector representation.

    :param text: The text to be embedded.
    :return: A list of floats representing the vector embedding.
    """
    global client

    if client is None:
        return [0.1, 0.2, 0.3, 0.4, 0.5] * 20

    response = client.embeddings(model="nomic-embed-text", prompt=text)  # type: ignore
    embedding = response["embedding"]
    embed = list(embedding)

    return embed
