from abc import ABC, abstractmethod
from dataclasses import dataclass
import typing as t

import google.generativeai as genai
import ollama
from flask import g


from ucr_chatbot.config import LLMMode, app_config


class PartDict(t.TypedDict, total=True):
    text: str


class ContentDict(t.TypedDict, total=True):
    role: t.Literal["user", "model"]
    parts: list[PartDict]


@dataclass
class ModelResponse:
    content: ContentDict

    def get_text(self) -> str:
        """The text body of this response."""
        return "\n".join([p["text"] for p in self.content["parts"]])


class LanguageModelClient(ABC):
    """An abstract base class for language model clients."""

    @abstractmethod
    def get_response(
        self, contents: list[ContentDict], max_tokens: int = 3000
    ) -> ModelResponse:
        """Gets a single, complete response from the language model.

        :param prompt: The prompt to feed into the language model.
        :param max_tokens: The maximal number of tokens to generate.
        :return: The completion from the language model.
        """
        pass


class TestingClient(LanguageModelClient):
    """A testing client that implements the LanguageModelClient interface.

    This client is used for testing purposes and returns predictable responses
    without requiring external API connections. It stores all parameters passed
    to it and returns formatted responses showing what was received.
    """

    def get_response(  # noqa: D102
        self, contents: list[ContentDict], max_tokens: int = 3000
    ) -> ModelResponse:
        response_parts = [
            f"You passed in arguments: contents='{contents}', max_tokens={max_tokens}"
        ]

        return ModelResponse(
            content=ContentDict(
                role="model", parts=[{"text": " | ".join(response_parts)}]
            )
        )


class Gemini(LanguageModelClient):
    """A class representation of the Gemini 2.5 Pro API."""

    def __init__(self, key: str):
        if not key:
            raise ValueError("A Gemini API key is required for production mode.")
        genai.configure(api_key=key)  # type: ignore
        self.model = genai.GenerativeModel(model_name="gemini-2.0-flash")  # type: ignore
        self.temp = 1.0

    def get_response(  # noqa: D102
        self, contents: list[ContentDict], max_tokens: int = 3000
    ) -> ModelResponse:
        config = {
            "temperature": self.temp,
            "max_output_tokens": max_tokens,
        }
        response = self.model.generate_content(contents, generation_config=config)  # type: ignore
        return ModelResponse(
            content=ContentDict(role="model", parts=[{"text": response.text}])
        )


class Ollama(LanguageModelClient):
    """A class representation for a local Ollama API."""

    def __init__(self, model: str = "gemma:2b", host: str = "http://localhost:11434"):
        """Initializes the Ollama client with the specified model and host.
        :param model: The name of the Ollama model to use.
        :param host: The host URL for the Ollama API.
        :raises ConnectionError: If the Ollama client cannot connect to the specified host."""
        self.model = model
        self.temp = 0.7
        try:
            self.client = ollama.Client(host=host)
            self.client.list()
        except Exception:
            raise ConnectionError(
                f"Could not connect to Ollama at {host}. Please ensure Ollama is running."
            )

    def get_response(  # noqa: D102
        self, contents: list[ContentDict], max_tokens: int = 3000
    ) -> ModelResponse:
        options = {
            "temperature": self.temp,
            "num_predict": max_tokens,
        }

        response = self.client.chat(  # type: ignore[reportUnknownMemberType]
            model=self.model,
            messages=list(map(self._convert_to_ollama_message, contents)),
            options=options,
            stream=False,
        )
        return ModelResponse(
            content=ContentDict(
                role="model", parts=[{"text": response.message.content or ""}]
            )
        )

    def _convert_to_ollama_message(self, content: ContentDict) -> ollama.Message:
        match content["role"]:
            case "user":
                role = "user"
            case "model":
                role = "assistant"

        assert len(content["parts"]) == 1

        return ollama.Message(role=role, content=content["parts"][0]["text"])


def get_language_model_client() -> LanguageModelClient:
    """Gets the language model client instance. Must be called from within a request context."""
    if g.get("_llm_client") is None:
        match app_config.LLM_MODE:
            case LLMMode.TESTING:
                g._llm_client = TestingClient()
            case LLMMode.OLLAMA:
                g._llm_client = Ollama(host=app_config.OLLAMA_URL)
            case LLMMode.GEMINI:
                if not app_config.GEMINI_API_KEY:
                    raise ValueError("GEMINI_API_KEY environment variable not set.")
                g._llm_client = Gemini(key=app_config.GEMINI_API_KEY)

    return g._llm_client
