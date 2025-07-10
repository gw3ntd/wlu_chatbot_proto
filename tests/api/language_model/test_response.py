import pytest
from unittest.mock import MagicMock, patch

# Adjust the import path to match your project structure
from ucr_chatbot.api.language_model.response import (
    LanguageModelClient,
    Gemini,
    Ollama,
)

# --- Test Gemini Class ---

@pytest.fixture
def mock_gemini_env(monkeypatch):
    """A pytest fixture to set up a mocked Gemini environment."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    # Mock the actual API call within the google library
    with patch("google.generativeai.GenerativeModel") as mock_model:
        # yield the mock so we can inspect it in tests
        yield mock_model

def test_gemini_init_success(mock_gemini_env):
    """Tests successful initialization of the Gemini client."""
    client = Gemini(key="fake-key")
    assert isinstance(client, LanguageModelClient)

def test_gemini_init_raises_error_without_key():
    """Tests that Gemini raises a ValueError if no API key is provided."""
    with pytest.raises(ValueError, match="A Gemini API key is required"):
        Gemini(key=None)

def test_gemini_get_response(mock_gemini_env):
    """Tests the get_response method for the Gemini client."""
    client = Gemini(key="fake-key")
    # Configure the mock model's return value
    mock_response = MagicMock()
    mock_response.text = "Gemini response text"
    client.model.generate_content.return_value = mock_response

    response = client.get_response("test prompt", max_tokens=100)
    assert response == "Gemini response text"
    # Verify that the underlying API call was made correctly
    client.model.generate_content.assert_called_once()

def test_gemini_stream_response(mock_gemini_env):
    """Tests the stream_response method for the Gemini client."""
    client = Gemini(key="fake-key")
    # Configure the mock model to return a generator of mock parts
    mock_part1 = MagicMock()
    mock_part1.text = "Stream part 1"
    mock_part2 = MagicMock()
    mock_part2.text = "Stream part 2"
    client.model.generate_content.return_value = iter([mock_part1, mock_part2])

    stream = client.stream_response("test prompt", max_tokens=100)
    result = "".join(list(stream))
    assert result == "Stream part 1Stream part 2"

def test_gemini_setters():
    """Tests the set_temp and set_stop_sequences methods for Gemini."""
    client = Gemini(key="fake-key")
    client.set_temp(0.5)
    client.set_stop_sequences(["stop"])
    assert client.temp == 0.5
    assert client.stop_sequences == ["stop"]

    with pytest.raises(ValueError):
        client.set_temp(3.0) # Out of range

# --- Test Ollama Class ---

@pytest.fixture
def mock_ollama_env(monkeypatch):
    """A pytest fixture to set up a mocked Ollama environment."""
    # Mock the ollama.Client so it doesn't make a real connection
    with patch("ollama.Client") as mock_client:
        yield mock_client

def test_ollama_init_success(mock_ollama_env):
    """Tests successful initialization of the Ollama client."""
    client = Ollama()
    assert isinstance(client, LanguageModelClient)
    # Check that it tried to connect by calling list()
    client.client.list.assert_called_once()

def test_ollama_init_raises_connection_error(monkeypatch):
    """Tests that Ollama raises ConnectionError if the client fails to connect."""
    # Make the ollama.Client constructor raise an exception
    monkeypatch.setattr("ollama.Client", MagicMock(side_effect=Exception("connection failed")))
    with pytest.raises(ConnectionError, match="Could not connect to Ollama"):
        Ollama()

def test_ollama_get_response(mock_ollama_env):
    """Tests the get_response method for the Ollama client."""
    client = Ollama()
    # Configure the mock client's return value
    client.client.generate.return_value = {"response": "Ollama response text"}

    response = client.get_response("test prompt", max_tokens=100)
    assert response == "Ollama response text"
    client.client.generate.assert_called_once()

def test_ollama_stream_response(mock_ollama_env):
    """Tests the stream_response method for the Ollama client."""
    client = Ollama()
    # Configure the mock client to return a generator of mock chunks
    mock_chunk1 = {"response": "Stream part 1"}
    mock_chunk2 = {"response": "Stream part 2"}
    client.client.generate.return_value = iter([mock_chunk1, mock_chunk2])

    stream = client.stream_response("test prompt", max_tokens=100)
    result = "".join(list(stream))
    assert result == "Stream part 1Stream part 2"

# --- Test Global Client Initialization ---

# def test_global_client_is_ollama_by_default(monkeypatch):
#     """Tests that the global client is an Ollama instance by default."""
#     monkeypatch.setattr("ollama.Client", MagicMock())
#     # We need to reload the module to trigger the initialization logic again
#     import importlib
#     import ucr_chatbot.api.language_model.response as response_module
#     importlib.reload(response_module)
#     assert response_module.client.__class__.__name__ == "Ollama"

def test_global_client_is_gemini_in_production(monkeypatch):
    """Tests that the global client is a Gemini instance in production mode."""
    monkeypatch.setenv("LLM_MODE", "production")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr("google.generativeai.GenerativeModel", MagicMock())

    import importlib
    import ucr_chatbot.api.language_model.response as response_module
    importlib.reload(response_module)
    assert response_module.client.__class__.__name__ == "Gemini"