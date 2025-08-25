import os
from dotenv import load_dotenv
from enum import Enum
from typing import no_type_check
from pathlib import PurePath

from flask import current_app
from authlib.integrations.flask_client import OAuth  # type: ignore

load_dotenv()


def get_non_empty_env[T](var_name: str, default: str | T = None) -> str | T:
    """Get the environment variable or return a default value. Default is returned if var_name is an empty string."""
    value = os.getenv(var_name, default)
    if value == "":
        return default
    return value


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


class FileStorageMode(Enum):
    """The mode in which the file storage is to run."""

    LOCAL = 1

    @staticmethod
    def from_str(enum_name: str) -> "FileStorageMode":
        """Creates a FileStorageMode from a string."""
        match enum_name.lower():
            case "local":
                return FileStorageMode.LOCAL
            case invalid_name:
                raise ValueError(f"Invalid file storage mode '{invalid_name}'")


class Config:
    """The global configuration for the UCR Chatbot."""

    SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32))

    DB_NAME = os.environ["DB_NAME"]
    DB_USER = os.environ["DB_USER"]
    DB_PASSWORD = os.environ["DB_PASSWORD"]
    DB_URL = os.environ["DB_URL"]

    GOOGLE_CLIENT_ID = get_non_empty_env("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = get_non_empty_env("GOOGLE_CLIENT_SECRET")

    REQUIRE_OAUTH = get_non_empty_env("REQUIRE_OAUTH", "true").lower() == "true"

    OLLAMA_URL = get_non_empty_env("OLLAMA_URL", "http://localhost:11434")
    GEMINI_API_KEY = get_non_empty_env("GEMINI_API_KEY")
    LLM_MODE = LLMMode.from_str(get_non_empty_env("LLM_MODE", "testing"))

    FILE_STORAGE_MODE = FileStorageMode.from_str(
        get_non_empty_env("FILE_STORAGE_MODE", "local")
    )
    FILE_STORAGE_PATH = get_non_empty_env("FILE_STORAGE_PATH", "storage")


class ConfigProxy:
    """A typed proxy for accessing Flask's configuration."""

    @property
    @no_type_check
    def SECRET_KEY(self) -> str | bytes:  # noqa: N802
        """The secret key for the Flask application."""
        return current_app.config["SECRET_KEY"]

    @property
    @no_type_check
    def DB_NAME(self) -> str:  # noqa: N802
        """The name of the database."""
        return current_app.config["DB_NAME"]

    @property
    @no_type_check
    def DB_USER(self) -> str:  # noqa: N802
        """The user for the database."""
        return current_app.config["DB_USER"]

    @property
    @no_type_check
    def DB_PASSWORD(self) -> str:  # noqa: N802
        """The password for the DB"""
        return current_app.config["DB_PASSWORD"]

    @property
    @no_type_check
    def DB_URL(self) -> str:  # noqa: N802
        """The database URL."""
        return current_app.config["DB_URL"]

    @property
    @no_type_check
    def GOOGLE_CLIENT_ID(self) -> str:  # noqa: N802
        """The client ID for Google OAuth."""
        return current_app.config["GOOGLE_CLIENT_ID"]

    @property
    @no_type_check
    def GOOGLE_CLIENT_SECRET(self) -> str:  # noqa: N802
        """The client secret for Google OAuth."""
        return current_app.config["GOOGLE_CLIENT_SECRET"]

    @property
    @no_type_check
    def REQUIRE_OAUTH(self) -> bool:  # noqa: N802
        """Whether OAUTH is the only acceptable form of user authentication."""
        return current_app.config["REQUIRE_OAUTH"]

    @property
    @no_type_check
    def OLLAMA_URL(self) -> str:  # noqa: N802
        """The URL for OLLAMA"""
        return current_app.config["OLLAMA_URL"]

    @property
    @no_type_check
    def GEMINI_API_KEY(self) -> str:  # noqa: N802
        """The API key for Google Gemini."""
        return current_app.config["GEMINI_API_KEY"]

    @property
    @no_type_check
    def LLM_MODE(self) -> LLMMode:  # noqa: N802
        """The type of LLM that is used."""
        return current_app.config["LLM_MODE"]

    @property
    @no_type_check
    def FILE_STORAGE_MODE(self) -> FileStorageMode:  # noqa: N802
        """The mode in which the file storage is to run."""
        return current_app.config["FILE_STORAGE_MODE"]

    @property
    @no_type_check
    def OAUTH_CLIENT(self) -> OAuth:  # noqa: N802
        """The OAuth client instance."""
        return current_app.config["OAUTH_CLIENT"]

    @property
    @no_type_check
    def FILE_STORAGE_PATH(self) -> PurePath:  # noqa: N802
        """The location where files are stored if relevant to the file storage mode."""
        return PurePath(current_app.config["FILE_STORAGE_PATH"])


app_config = ConfigProxy()
"""A global instance of the ConfigProxy for accessing application configuration values."""
