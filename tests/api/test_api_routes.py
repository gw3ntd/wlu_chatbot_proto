import pytest
import json
from unittest.mock import MagicMock

def test_generate_non_stream_success(client, monkeypatch):
    """
    Tests a successful non-streaming POST request to /generate.
    Uses TestingClient for language model but mocks retriever to avoid database issues.
    """
    # Mock the retriever to avoid database connection issues
    mock_retriever = MagicMock()
    mock_segments = [
        MagicMock(id=1, text="First relevant context"),
        MagicMock(id=2, text="Second relevant context"),
        MagicMock(id=3, text="Third relevant context")
    ]
    mock_retriever.get_segments_for.return_value = mock_segments
    monkeypatch.setattr("ucr_chatbot.api.routes.retriever", mock_retriever)

    # Make the request to the endpoint
    response = client.post(
        '/api/generate',
        json={"prompt": "What is Python?", "conversation_id": 55}
    )

    # Assert the results
    assert response.status_code == 200
    response_data = response.get_json()
    
    # Verify response structure
    assert "text" in response_data
    assert "conversation_id" in response_data
    assert "sources" in response_data
    
    # Verify response values
    assert response_data["conversation_id"] == 55
    assert "You passed in arguments" in response_data["text"]
    assert "What is Python?" in response_data["text"]
    
    # Verify retriever was called
    mock_retriever.get_segments_for.assert_called_once_with("What is Python?", 0, num_segments=3)


def test_generate_stream_success(client, monkeypatch):
    """
    Tests a successful streaming POST request to /generate.
    Uses TestingClient for language model but mocks retriever to avoid database issues.
    """
    # Mock the retriever to avoid database connection issues
    mock_retriever = MagicMock()
    mock_retriever.get_segments_for.return_value = []
    monkeypatch.setattr("ucr_chatbot.api.routes.retriever", mock_retriever)

    response = client.post(
        '/api/generate',
        json={"prompt": "Tell me a story", "stream": True, "conversation_id": 56}
    )

    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"
    
    # Verify the server-sent event formatting
    response_data = response.get_data(as_text=True)
    assert "data: " in response_data
    assert "You passed in arguments" in response_data
    assert "Tell me a story" in response_data


def test_generate_passes_parameters_to_client(client, monkeypatch):
    """
    Tests that optional parameters are correctly extracted from the JSON
    and passed to the language model client.
    Uses TestingClient to verify parameters are passed correctly.
    """
    # Mock the retriever to avoid database connection issues
    mock_retriever = MagicMock()
    mock_retriever.get_segments_for.return_value = []
    monkeypatch.setattr("ucr_chatbot.api.routes.retriever", mock_retriever)

    response = client.post(
        '/api/generate',
        json={
            "prompt": "test",
            "temperature": 0.99,
            "max_tokens": 512,
            "stop_sequences": ["\n", "User:"]
        }
    )

    assert response.status_code == 200
    response_data = response.get_json()
    
    # Verify that the TestingClient received and formatted the parameters
    assert "temperature=0.99" in response_data["text"]
    assert "max_tokens=512" in response_data["text"]
    assert "stop_sequences=" in response_data["text"]


def test_generate_with_all_parameters(client, monkeypatch):
    """
    Tests the /api/generate endpoint with ALL valid parameters to ensure
    comprehensive coverage of the API functionality.
    Uses TestingClient for language model but mocks retriever to avoid database issues.
    """
    # Mock the retriever to avoid database connection issues
    mock_retriever = MagicMock()
    mock_segments = [
        MagicMock(id=1, text="First relevant context"),
        MagicMock(id=2, text="Second relevant context"),
        MagicMock(id=3, text="Third relevant context")
    ]
    mock_retriever.get_segments_for.return_value = mock_segments
    monkeypatch.setattr("ucr_chatbot.api.routes.retriever", mock_retriever)

    # Test with ALL valid parameters
    request_data = {
        "prompt": "What is the difference between Python and JavaScript?",
        "conversation_id": 12345,
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 1500,
        "stop_sequences": ["\n\n", "Question:", "Answer:"]
    }

    response = client.post('/api/generate', json=request_data)

    # Assert response status and structure
    assert response.status_code == 200
    response_data = response.get_json()
    
    # Verify response contains expected fields
    assert "text" in response_data
    assert "sources" in response_data
    assert "conversation_id" in response_data
    
    # Verify response values
    assert response_data["conversation_id"] == 12345
    assert "You passed in arguments" in response_data["text"]
    assert "What is the difference between Python and JavaScript?" in response_data["text"]
    assert "temperature=0.7" in response_data["text"]
    assert "max_tokens=1500" in response_data["text"]
    assert "stop_sequences=" in response_data["text"]


def test_generate_missing_prompt_returns_400(client):
    """
    Tests that a 400 Bad Request error is returned if 'prompt' is missing.
    """
    response = client.post('/api/generate', json={"conversation_id": 1})
    assert response.status_code == 400
    response_data = response.get_json()
    assert "Missing 'prompt' in request" in response_data["error"]


def test_generate_invalid_json_returns_400(client):
    """
    Tests that a 400 Bad Request error is returned for a non-JSON request body.
    """
    response = client.post(
        '/api/generate',
        data="this is not json",
        content_type="text/plain"
    )
    assert response.status_code == 415
