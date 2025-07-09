import pytest
import json
from unittest.mock import MagicMock

# You'll need to create a Flask app fixture, often in a conftest.py file
# For simplicity, we'll define it here.
from your_project.app import create_app # Assuming you have an app factory
from your_project.api.routes import bp as api_routes

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.register_blueprint(api_routes, url_prefix='/api')
    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


# --- Comprehensive Test Cases ---

def test_generate_non_stream_ok(client, monkeypatch):
    """
    Tests a successful non-streaming POST request to /generate.
    """
    # 1. Mock the dependencies that the route calls
    mock_retriever = MagicMock()
    # Mock the segment object that the retriever returns
    mock_segment = MagicMock()
    mock_segment.segment_id = 101
    mock_segment.text = "Mocked context text."
    mock_retriever.get_segments_for.return_value = [mock_segment]

    # Mock the language model function
    mock_get_response = MagicMock(return_value="This is the mocked LLM response.")

    monkeypatch.setattr("your_project.api.routes.retriever", mock_retriever)
    monkeypatch.setattr("your_project.api.routes.get_response_from_prompt", mock_get_response)

    # 2. Make the request to the endpoint
    response = client.post(
        '/api/generate',
        json={"prompt": "What is Python?", "conversation_id": 123}
    )

    # 3. Assert the results
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["text"] == "This is the mocked LLM response."
    assert response_data["conversation_id"] == 123
    assert response_data["sources"][0]["segment_id"] == 101


def test_generate_stream_ok(client, monkeypatch):
    """
    Tests a successful streaming POST request to /generate.
    """
    # Mock the streaming function to return a simple generator
    mock_stream_response = MagicMock(return_value=iter(["Mock ", "stream ", "response."]))
    monkeypatch.setattr("your_project.api.routes.stream_response_from_prompt", mock_stream_response)

    # Mock the retriever (it's called before the stream flag is checked)
    monkeypatch.setattr("your_project.api.routes.retriever.get_segments_for", MagicMock(return_value=[]))

    response = client.post(
        '/api/generate',
        json={"prompt": "Tell me a story", "stream": True}
    )

    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"
    # Check if the streamed content is what we expect
    expected_data = 'data: {"text": "Mock "}\n\ndata: {"text": "stream "}\n\ndata: {"text": "response."}\n\n'
    assert response.get_data(as_text=True) == expected_data


def test_generate_missing_prompt_error(client):
    """
    Tests that a 400 Bad Request error is returned if 'prompt' is missing.
    """
    response = client.post(
        '/api/generate',
        json={"conversation_id": 1} # Missing the 'prompt' key
    )
    assert response.status_code == 400
    response_data = response.get_json()
    assert "error" in response_data
    assert "Missing 'prompt' in request" in response_data["error"]


def test_generate_passes_parameters_to_llm(client, monkeypatch):
    """
    Tests that optional parameters (temperature, max_tokens) are correctly
    passed from the JSON request to the language model function.
    """
    # We only need to mock the language model function for this test
    mock_get_response = MagicMock()
    monkeypatch.setattr("your_project.api.routes.get_response_from_prompt", mock_get_response)
    monkeypatch.setattr("your_project.api.routes.retriever.get_segments_for", MagicMock(return_value=[]))

    # Make a request with optional parameters
    client.post(
        '/api/generate',
        json={
            "prompt": "test",
            "conversation_id": 1,
            "temperature": 0.95,
            "max_tokens": 500
        }
    )

    # Assert that our mock function was called with the correct arguments
    mock_get_response.assert_called_once()
    call_args, call_kwargs = mock_get_response.call_args
    assert call_kwargs['temperature'] == 0.95
    assert call_kwargs['max_tokens'] == 500
