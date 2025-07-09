# We recommend installing an extension to run python tests.


def test_stream_response_from_prompt_return_type():
    """Tests that the streaming function returns an iterable of strings."""
    stream = stream_response_from_prompt("Where did you come from?")
    assert isinstance(stream, Iterable)
    for s in stream:
        assert isinstance(s, str)
    # The stream is lazy, so we don't iterate here in this simple test.

# --- Comprehensive Mocked Tests ---

def test_get_response_in_testing_mode(monkeypatch):
    """
    Ensures the function calls the Ollama client in 'testing' mode.
    """
    # Create a fake Ollama client
    mock_ollama_client = MagicMock()
    # Tell its 'get_response' method what to return
    mock_ollama_client.get_response.return_value = "Ollama response"

    # When Ollama is initialized, make it return our fake client
    monkeypatch.setattr("ucr_chatbot.api.language_model.Ollama", lambda **kwargs: mock_ollama_client)
    # Force the mode to 'testing'
    monkeypatch.setenv("LLM_MODE", "testing")

    # Call the function we are testing
    response = get_response_from_prompt("test prompt")

    # Assertions
    assert response == "Ollama response"
    mock_ollama_client.get_response.assert_called_once_with("test prompt", ANY)


def test_get_response_in_production_mode(monkeypatch):
    """
    Ensures the function calls the Gemini client in 'production' mode.
    """
    mock_gemini_client = MagicMock()
    mock_gemini_client.get_response.return_value = "Gemini response"

    monkeypatch.setattr("ucr_chatbot.api.language_model.Gemini", lambda **kwargs: mock_gemini_client)
    monkeypatch.setenv("LLM_MODE", "production")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-api-key") # Must be present

    response = get_response_from_prompt("test prompt")

    assert response == "Gemini response"
    mock_gemini_client.get_response.assert_called_once_with("test prompt", ANY)


def test_stream_response_in_testing_mode(monkeypatch):
    """
    Ensures the streaming function calls the Ollama client correctly.
    """
    mock_ollama_client = MagicMock()
    # Make the stream_response method return a simple generator
    mock_ollama_client.stream_response.return_value = iter(["Ollama ", "stream ", "response"])

    monkeypatch.setattr("ucr_chatbot.api.language_model.Ollama", lambda **kwargs: mock_ollama_client)
    monkeypatch.setenv("LLM_MODE", "testing")

    # Call the function and consume the generator
    stream = stream_response_from_prompt("test stream")
    result = "".join(list(stream))

    assert result == "Ollama stream response"
    mock_ollama_client.stream_response.assert_called_once_with("test stream", ANY)


def test_production_mode_raises_error_without_key(monkeypatch):
    """
    Tests that running in 'production' mode without an API key raises a ValueError.
    """
    # Force production mode but remove the API key
    monkeypatch.setenv("LLM_MODE", "production")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # Use pytest.raises to assert that a specific error is thrown
    with pytest.raises(ValueError, match="A Gemini API key is required"):
        get_response_from_prompt("this will fail")


def test_parameters_are_passed_correctly(monkeypatch):
    """
    Tests that optional parameters like temperature are passed down to the client.
    """
    mock_gemini_client = MagicMock()
    monkeypatch.setattr("ucr_chatbot.api.language_model.Gemini", lambda **kwargs: mock_gemini_client)
    monkeypatch.setenv("LLM_MODE", "production")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-api-key")

    # Call the function with specific keyword arguments
    get_response_from_prompt(
        "test prompt",
        max_tokens=500,
        temperature=0.9,
        stop_sequences=["stop"]
    )

    # We can't easily inspect the kwargs of the client's init,
    # but we can test the factory function directly.
    client_instance = get_llm_client(temperature=0.9, stop_sequences=["stop"])

    # Assert that the client object was created with the correct attributes
    assert isinstance(client_instance, Gemini)
    assert client_instance.temperature == 0.9
    assert client_instance.stop_sequences == ["stop"]
