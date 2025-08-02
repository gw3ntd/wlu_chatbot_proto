import os
from dotenv import load_dotenv
from enum import Enum
from pathlib import Path

load_dotenv()


class LLMMode(Enum):
    """The mode in which the LLM is to run."""

    TESTING = 1
    GEMINI = 2
    OLLAMA = 3

    @staticmethod
    def from_str(enum_name: str) -> "LLMMode":
        """Creates an LLMMode from a string."""
        match enum_name.lower():
            case "testing":
                return LLMMode.TESTING
            case "gemini":
                return LLMMode.GEMINI
            case "ollama":
                return LLMMode.OLLAMA
            case invalid_name:
                raise ValueError(f"Invalid LLM mode '{invalid_name}'")


class Config:
    """The global configuration for the UCR Chatbot."""

    SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32))

    DB_NAME = os.environ["DB_NAME"]
    DB_USER = os.environ["DB_USER"]
    DB_PASSWORD = os.environ["DB_PASSWORD"]
    DB_URL = os.environ["DB_URL"]

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_SECRET = os.getenv("GOOGLE_SECRET")

    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    LLM_MODE = LLMMode.from_str(os.getenv("LLM_MODE", "testing"))

    FILE_STORAGE_PATH = Path(
        os.getenv("FILE_STORAGE_PATH", Path(__file__).parent / "db" / "uploads")
    )
