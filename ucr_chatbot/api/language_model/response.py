from typing import Generator


def get_response_from_prompt(prompt: str) -> str:
    """Gets a response from a language model.

    :param prompt: The prompt to feed into the language model.
    :return: The completion from the language model.
    """
    return f"Echoing: {prompt}"


def stream_response_from_prompt(prompt: str) -> Generator[str]:
    """Streams a response from a language.

    :param prompt: The prompt to feed into the language model.
    :yield: The next substring of the language model's completion
    """
    yield from f"Streamed Echoing: {prompt}"
