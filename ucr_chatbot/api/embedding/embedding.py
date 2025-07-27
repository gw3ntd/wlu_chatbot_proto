from typing import Sequence
from ollama import Client
from ..language_model.response import MODE

OLLAMA_URL = "localhost:11434"

if MODE == "dog":
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

    response = client.embeddings(model="nomic-embed-text", prompt=text)  # type: ignore
    embedding = response["embedding"]
    embed = list(embedding)

    return embed
