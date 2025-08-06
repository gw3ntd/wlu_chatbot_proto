import google.generativeai as genai
import ollama
from typing import Generator, List, Any
from abc import ABC, abstractmethod
from ucr_chatbot.config import Config, LLMMode


class LanguageModelClient(ABC):
    """An abstract base class for language model clients."""

    @abstractmethod
    def get_response(self, prompt: str, max_tokens: int = 3000) -> str:
        """Gets a single, complete response from the language model.

        :param prompt: The prompt to feed into the language model.
        :param max_tokens: The maximal number of tokens to generate.
        :return: The completion from the language model.
        """
        pass

    @abstractmethod
    def stream_response(
        self, prompt: str, max_tokens: int = 3000
    ) -> Generator[str, None, None]:
        """Streams a response from the language model.
        :param prompt: The prompt to feed into the language model.
        :param max_tokens: The maximal number of tokens to generate.
        :return: A generator yielding parts of the response."""
        pass

    @abstractmethod
    def set_temp(self, temp: float) -> None:
        """Sets the generation temperature for the model.
        :param temp: The temperature for generation, between 0.0 and 2.0.
        :raises ValueError: If the temperature is not in the valid range."""
        pass

    @abstractmethod
    def set_stop_sequences(self, stop: List[str]) -> None:
        """Sets the stop sequences for the model.
        :param stop: A list of strings that will stop the generation when encountered.
        :raises TypeError: If stop is not a list of strings.
        :raises ValueError: If the list contains more than 5 items."""

        pass


class TestingClient(LanguageModelClient):
    """A testing client that implements the LanguageModelClient interface.

    This client is used for testing purposes and returns predictable responses
    without requiring external API connections. It stores all parameters passed
    to it and returns formatted responses showing what was received.
    """

    def __init__(self):
        """Initialize the testing client with default values."""
        self.temp: float = 1.0
        self.stop_sequences: List[str] = []
        self.last_prompt: str | None = None
        self.last_max_tokens: int | None = None
        self.last_temperature: float | None = None
        self.last_stop_sequences: List[str] | None = None

    def get_response(self, prompt: str, max_tokens: int = 3000, **kwargs: Any) -> str:
        """Gets a single response from the testing client.

        :param prompt: The prompt to feed into the language model.
        :param max_tokens: The maximal number of tokens to generate.
        :param kwargs: Additional keyword arguments (temperature, stop_sequences, etc.)
        :return: A formatted string showing the parameters that were passed.
        """
        # Store the parameters for testing purposes
        self.last_prompt = prompt
        self.last_max_tokens = max_tokens
        self.last_temperature = kwargs.get("temperature", self.temp)
        self.last_stop_sequences = kwargs.get("stop_sequences", self.stop_sequences)

        # Return a formatted response showing what was passed
        response_parts = [
            f"You passed in arguments: prompt='{prompt}', max_tokens={max_tokens}"
        ]

        if "temperature" in kwargs:
            response_parts.append(f"temperature={kwargs['temperature']}")
        if "stop_sequences" in kwargs:
            response_parts.append(f"stop_sequences={kwargs['stop_sequences']}")

        return " | ".join(response_parts)

    def stream_response(
        self, prompt: str, max_tokens: int = 3000, **kwargs: Any
    ) -> Generator[str, None, None]:
        """Streams a response from the testing client.

        :param prompt: The prompt to feed into the language model.
        :param max_tokens: The maximal number of tokens to generate.
        :param kwargs: Additional keyword arguments (temperature, stop_sequences, etc.)
        :yields: A generator yielding parts of the response.
        """
        # Store the parameters for testing purposes
        self.last_prompt = prompt
        self.last_max_tokens = max_tokens
        self.last_temperature = kwargs.get("temperature", self.temp)
        self.last_stop_sequences = kwargs.get("stop_sequences", self.stop_sequences)

        # Yield a formatted response showing what was passed
        response_parts = [
            f"You passed in arguments: prompt='{prompt}', max_tokens={max_tokens}"
        ]

        if "temperature" in kwargs:
            response_parts.append(f"temperature={kwargs['temperature']}")
        if "stop_sequences" in kwargs:
            response_parts.append(f"stop_sequences={kwargs['stop_sequences']}")

        full_response = " | ".join(response_parts)

        # Split the response into chunks for streaming
        words = full_response.split()
        chunk_size = max(1, len(words) // 3)  # Split into roughly 3 chunks

        for i in range(0, len(words), chunk_size):
            chunk_words = words[i : i + chunk_size]
            yield " ".join(chunk_words) + (" " if i + chunk_size < len(words) else "")

    def set_temp(self, temp: float) -> None:
        """Sets the generation temperature for the model.

        :param temp: The temperature for generation, between 0.0 and 2.0.
        :raises ValueError: If the temperature is not in the valid range.
        """
        if not (0.0 <= temp <= 2.0):
            raise ValueError("Temperature must be between 0.0 and 2.0.")
        self.temp = temp

    def set_stop_sequences(self, stop: List[str]) -> None:
        """Sets the stop sequences for the model.

        :param stop: A list of strings that will stop the generation when encountered.
        :raises TypeError: If stop is not a list of strings.
        :raises ValueError: If the list contains more than 5 items.
        """
        if len(stop) > 5:
            raise ValueError(
                "The list of stop sequences cannot contain more than 5 items."
            )
        self.stop_sequences = stop


# --- Client Classes ---
class Gemini(LanguageModelClient):
    """A class representation of the Gemini 2.5 Pro API."""

    def __init__(self, key: str):
        if not key:
            raise ValueError("A Gemini API key is required for production mode.")
        genai.configure(api_key=key)  # type: ignore
        self.model = genai.GenerativeModel(model_name="gemini-2.0-flash")  # type: ignore ----------------------------------------------------CHANGE!
        self.temp = 1.0
        self.stop_sequences = []

    def get_response(self, prompt: str, max_tokens: int = 3000, **kwargs: Any) -> str:
        """Gets a response by calling the currently configured global client.

        :param prompt: The prompt to feed into the language model.
        :param max_tokens: The maximal number of tokens generated by the language model.
        :return: The completion from the language model.
        """

        if "temperature" in kwargs:
            self.temp = kwargs["temperature"]
        if "stop_sequences" in kwargs:
            self.stop_sequences = kwargs["stop_sequences"]

        config = {
            "temperature": self.temp,
            "max_output_tokens": max_tokens,
            "stop_sequences": self.stop_sequences,
        }
        response = self.model.generate_content(prompt, generation_config=config)  # type: ignore
        return response.text

    def stream_response(
        self, prompt: str, max_tokens: int = 3000
    ) -> Generator[str, None, None]:
        """Streams a response from the Gemini model.
        :param prompt: The prompt to feed into the language model.
        :param max_tokens: The maximal number of tokens to generate.
        :yields: A generator yielding parts of the response."""
        config = {
            "temperature": self.temp,
            "max_output_tokens": max_tokens,
            "stop_sequences": self.stop_sequences,
        }
        response = self.model.generate_content(  # type: ignore
            prompt,
            generation_config=config,  # type: ignore
            stream=True,
        )
        for part in response:
            yield part.text

    def set_temp(self, temp: float) -> None:
        """Sets the generation temperature for the model.
        :param temp: The temperature for generation, between 0.0 and 2.0.
        :raises ValueError: If the temperature is not in the valid range."""
        if not (0.0 <= temp <= 2.0):
            raise ValueError("Temperature must be between 0.0 and 2.0.")
        self.temp = temp

    def set_stop_sequences(self, stop: List[str]) -> None:
        """Sets the stop sequences for the model.
        :param stop: A list of strings that will stop the generation when encountered.
        :raises TypeError: If stop is not a list of strings.
        :raises ValueError: If the list contains more than 5 items."""
        if len(stop) > 5:
            raise ValueError(
                "The list of stop sequences cannot contain more than 5 items."
            )
        self.stop_sequences = stop


class Ollama(LanguageModelClient):
    """A class representation for a local Ollama API."""

    def __init__(self, model: str = "gemma:2b", host: str = "http://localhost:11434"):
        """Initializes the Ollama client with the specified model and host.
        :param model: The name of the Ollama model to use.
        :param host: The host URL for the Ollama API.
        :raises ConnectionError: If the Ollama client cannot connect to the specified host."""
        self.model = model
        self.temp = 0.7
        self.stop_sequences = None
        try:
            self.client = ollama.Client(host=host)
            self.client.list()
        except Exception:
            raise ConnectionError(
                f"Could not connect to Ollama at {host}. Please ensure Ollama is running."
            )

    def get_response(self, prompt: str, max_tokens: int = 3000) -> str:
        """Gets a single response from the Ollama model.
        :param prompt: The prompt to feed into the language model.
        :param max_tokens: The maximal number of tokens to generate.
        :return: A string containing the model's complete response."""
        options = {
            "temperature": self.temp,
            "num_predict": max_tokens,
            "stop": self.stop_sequences,
        }
        response = self.client.generate(
            model=self.model, prompt=prompt, stream=False, options=options
        )
        return response.get("response", "")

    def stream_response(
        self, prompt: str, max_tokens: int = 3000
    ) -> Generator[str, None, None]:
        """Streams a response from the Ollama model.
        :param prompt: The prompt to feed into the language model.
        :param max_tokens: The maximal number of tokens to generate.
        :yields: A generator yielding parts of the response."""
        options = {
            "temperature": self.temp,
            "num_predict": max_tokens,
            "stop": self.stop_sequences,
        }
        stream = self.client.generate(
            model=self.model, prompt=prompt, stream=True, options=options
        )
        for chunk in stream:
            yield chunk.get("response", "")

    def set_temp(self, temp: float) -> None:
        """Sets the generation temperature for the model.
        param temp: The temperature for generation, between 0.0 and 2.0."""
        self.temp = temp

    def set_stop_sequences(self, stop: List[str]) -> None:
        """Sets the stop sequences for the model.
        :param stop: A list of strings that will stop the generation when encountered.
        :raises TypeError: If stop is not a list of strings."""
        self.stop_sequences = stop


match Config.LLM_MODE:
    case LLMMode.TESTING:
        client = TestingClient()
    case LLMMode.OLLAMA:
        client = Ollama(host=Config.OLLAMA_URL)
    case LLMMode.GEMINI:
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        client: LanguageModelClient = Gemini(key=Config.GEMINI_API_KEY)
