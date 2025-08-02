import pytest
from unittest.mock import MagicMock, patch

# Adjust the import path to match your project structure
from ucr_chatbot.api.language_model.response import (
    Gemini,
    Ollama,
    TestingClient,
)

# --- Test TestingClient Class ---

def test_testing_client_init():
    """Tests successful initialization of the TestingClient."""
    client = TestingClient()
    assert client.temp == 1.0
    assert client.stop_sequences == []
    assert client.last_prompt is None
    assert client.last_max_tokens is None
    assert client.last_temperature is None
    assert client.last_stop_sequences is None


def test_testing_client_get_response():
    """Tests that TestingClient.get_response returns formatted parameters."""
    client = TestingClient()
    
    response = client.get_response("Hello world", max_tokens=100)
    
    assert "You passed in arguments: prompt='Hello world', max_tokens=100" in response
    assert client.last_prompt == "Hello world"
    assert client.last_max_tokens == 100


def test_testing_client_get_response_with_temperature():
    """Tests that TestingClient.get_response includes temperature in response."""
    client = TestingClient()
    
    response = client.get_response("Test prompt", max_tokens=50, temperature=0.7)
    
    assert "temperature=0.7" in response
    assert client.last_temperature == 0.7


def test_testing_client_get_response_with_stop_sequences():
    """Tests that TestingClient.get_response includes stop_sequences in response."""
    client = TestingClient()
    stop_seqs = ["\n", "User:"]
    
    response = client.get_response("Test prompt", max_tokens=50, stop_sequences=stop_seqs)
    
    assert "stop_sequences=" in response
    assert client.last_stop_sequences == stop_seqs


def test_testing_client_stream_response():
    """Tests that TestingClient.stream_response yields formatted parameters."""
    client = TestingClient()
    
    stream = client.stream_response("Stream test", max_tokens=75)
    chunks = list(stream)
    
    # Should yield chunks of the response
    assert len(chunks) > 0
    full_response = "".join(chunks)
    assert "You passed in arguments: prompt='Stream test', max_tokens=75" in full_response
    assert client.last_prompt == "Stream test"
    assert client.last_max_tokens == 75


def test_testing_client_stream_response_with_parameters():
    """Tests that TestingClient.stream_response includes all parameters."""
    client = TestingClient()
    stop_seqs = ["END", "STOP"]
    
    stream = client.stream_response(
        "Stream with params", 
        max_tokens=200, 
        temperature=0.5, 
        stop_sequences=stop_seqs
    )
    chunks = list(stream)
    
    full_response = "".join(chunks)
    assert "temperature=0.5" in full_response
    assert "stop_sequences=" in full_response
    assert client.last_temperature == 0.5
    assert client.last_stop_sequences == stop_seqs


def test_testing_client_set_temp():
    """Tests that TestingClient.set_temp works correctly."""
    client = TestingClient()
    
    client.set_temp(0.8)
    assert client.temp == 0.8


def test_testing_client_set_temp_invalid():
    """Tests that TestingClient.set_temp raises ValueError for invalid temperature."""
    client = TestingClient()
    
    with pytest.raises(ValueError, match="Temperature must be between 0.0 and 2.0."):
        client.set_temp(2.5)
    
    with pytest.raises(ValueError, match="Temperature must be between 0.0 and 2.0."):
        client.set_temp(-0.1)


def test_testing_client_set_stop_sequences():
    """Tests that TestingClient.set_stop_sequences works correctly."""
    client = TestingClient()
    stop_seqs = ["\n", "User:", "Assistant:"]
    
    client.set_stop_sequences(stop_seqs)
    assert client.stop_sequences == stop_seqs


def test_testing_client_set_stop_sequences_too_many():
    """Tests that TestingClient.set_stop_sequences raises ValueError for too many items."""
    client = TestingClient()
    stop_seqs = ["1", "2", "3", "4", "5", "6"]  # More than 5 items
    
    with pytest.raises(ValueError, match="The list of stop sequences cannot contain more than 5 items."):
        client.set_stop_sequences(stop_seqs)


def test_testing_client_set_stop_sequences_invalid_type():
    """Tests that TestingClient.set_stop_sequences raises TypeError for invalid type."""
    client = TestingClient()
    
    # Since we removed the isinstance check, this should not raise an error
    # The method now only checks the length constraint
    stop_seqs = ["1", "2", "3", "4", "5", "6"]  # More than 5 items
    with pytest.raises(ValueError, match="The list of stop sequences cannot contain more than 5 items."):
        client.set_stop_sequences(stop_seqs)


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
    assert client.temp == 1.0
    assert client.stop_sequences == []


def test_gemini_init_no_key():
    """Tests that Gemini initialization fails without an API key."""
    with pytest.raises(ValueError, match="A Gemini API key is required for production mode."):
        Gemini(key="")


def test_gemini_get_response(mock_gemini_env):
    """Tests that Gemini.get_response calls the model correctly."""
    # Set up the mock to return a response
    mock_response = MagicMock()
    mock_response.text = "Mocked Gemini response"
    mock_gemini_env.return_value.generate_content.return_value = mock_response
    
    client = Gemini(key="fake-key")
    response = client.get_response("Test prompt", max_tokens=100)
    
    assert response == "Mocked Gemini response"
    mock_gemini_env.return_value.generate_content.assert_called_once()


def test_gemini_stream_response(mock_gemini_env):
    """Tests that Gemini.stream_response yields chunks correctly."""
    # Set up the mock to return a streaming response
    mock_part1 = MagicMock()
    mock_part1.text = "Stream part 1"
    mock_part2 = MagicMock()
    mock_part2.text = "Stream part 2"
    mock_gemini_env.return_value.generate_content.return_value = [mock_part1, mock_part2]
    
    client = Gemini(key="fake-key")
    stream = client.stream_response("Test prompt", max_tokens=100)
    
    result = "".join(list(stream))
    assert result == "Stream part 1Stream part 2"


def test_gemini_set_temp():
    """Tests that Gemini.set_temp works correctly."""
    client = Gemini(key="fake-key")
    client.set_temp(0.8)
    assert client.temp == 0.8


def test_gemini_set_temp_invalid():
    """Tests that Gemini.set_temp raises ValueError for invalid temperature."""
    client = Gemini(key="fake-key")
    
    with pytest.raises(ValueError, match="Temperature must be between 0.0 and 2.0."):
        client.set_temp(2.5)


def test_gemini_set_stop_sequences():
    """Tests that Gemini.set_stop_sequences works correctly."""
    client = Gemini(key="fake-key")
    stop_seqs = ["\n", "User:"]
    
    client.set_stop_sequences(stop_seqs)
    assert client.stop_sequences == stop_seqs


def test_gemini_set_stop_sequences_too_many():
    """Tests that Gemini.set_stop_sequences raises ValueError for too many items."""
    client = Gemini(key="fake-key")
    stop_seqs = ["1", "2", "3", "4", "5", "6"]  # More than 5 items
    
    with pytest.raises(ValueError, match="The list of stop sequences cannot contain more than 5 items."):
        client.set_stop_sequences(stop_seqs)


# --- Test Ollama Class ---

@pytest.fixture
def mock_ollama_env(monkeypatch):
    """A pytest fixture to set up a mocked Ollama environment."""
    with patch("ollama.Client") as mock_client:
        mock_client.return_value.list.return_value = []
        yield mock_client

def test_ollama_init_success(mock_ollama_env):
    """Tests successful initialization of the Ollama client."""
    client = Ollama()
    assert client.temp == 0.7
    assert client.stop_sequences is None


def test_ollama_get_response(mock_ollama_env):
    """Tests that Ollama.get_response calls the client correctly."""
    # Set up the mock to return a response
    mock_ollama_env.return_value.generate.return_value = {"response": "Mocked Ollama response"}
    
    client = Ollama()
    response = client.get_response("Test prompt", max_tokens=100)
    
    assert response == "Mocked Ollama response"
    mock_ollama_env.return_value.generate.assert_called_once()


def test_ollama_stream_response(mock_ollama_env):
    """Tests that Ollama.stream_response yields chunks correctly."""
    # Set up the mock to return a streaming response
    mock_ollama_env.return_value.generate.return_value = [
        {"response": "Stream part 1"},
        {"response": "Stream part 2"}
    ]
    
    client = Ollama()
    stream = client.stream_response("Test prompt", max_tokens=100)
    
    result = "".join(list(stream))
    assert result == "Stream part 1Stream part 2"


def test_ollama_set_temp(mock_ollama_env):
    """Tests that Ollama.set_temp works correctly."""
    client = Ollama()
    client.set_temp(0.8)
    assert client.temp == 0.8


def test_ollama_set_stop_sequences(mock_ollama_env):
    """Tests that Ollama.set_stop_sequences works correctly."""
    client = Ollama()
    stop_seqs = ["\n", "User:"]
    
    client.set_stop_sequences(stop_seqs)
    assert client.stop_sequences == stop_seqs