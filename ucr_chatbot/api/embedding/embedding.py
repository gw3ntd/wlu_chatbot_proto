from typing import Sequence
from ollama import Client
from ..language_model.response import MODE

OLLAMA_URL = "localhost:11434"

if MODE == "testing":
    client = None
else:
    try:
        client = Client(host=OLLAMA_URL)
        # A quick check to make sure the server is responsive
        client.list()
    except Exception as e:
        # This provides a more informative, specific error
        raise ConnectionError(f"Could not connect to Ollama at {OLLAMA_URL}") from e


def embed_text(text: str) -> Sequence[float]:
    """Embeds a string of text into a vector representation.

    :param text: The text to be embedded.
    :return: A list of floats representing the vector embedding.
    """
    global client

    # In testing mode, return a mock embedding
    if client is None:
        # Return a simple mock embedding for testing
        return [0.1, 0.2, 0.3, 0.4, 0.5] * 20  # 100-dimensional mock embedding

    response = client.embeddings(model="nomic-embed-text", prompt=text)  # type: ignore
    embedding = response["embedding"]
    embed = list(embedding)

    return embed
