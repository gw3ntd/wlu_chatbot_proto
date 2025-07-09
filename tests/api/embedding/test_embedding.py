import pytest
from unittest.mock import MagicMock
from ucr_chatbot.api.embedding.embedding import embed_text

def test_embed_text_success(monkeypatch):
    """
    Tests that embed_text correctly calls the client and returns a list of floats.
    """
    # 1. Create a fake Ollama client object
    mock_ollama_client = MagicMock()

    # 2. Configure the fake client's 'embeddings' method to return a predictable dictionary
    fake_embedding = [0.1, -0.2, 0.3, 0.4]
    mock_ollama_client.embeddings.return_value = {"embedding": fake_embedding}

    # 3. Use monkeypatch to replace the real 'client' in your embedding module with our fake one
    monkeypatch.setattr("ucr_chatbot.api.embedding.embedding.client", mock_ollama_client)

    # 4. Call the function we are testing
    result = embed_text("This input text doesn't matter because the client is mocked")

    # 5. Assert that the function behaved as expected
    assert isinstance(result, list)
    assert result == fake_embedding
    assert all(isinstance(x, float) for x in result)

    # 6. Assert that the underlying client method was called correctly
    mock_ollama_client.embeddings.assert_called_once_with(
        model="nomic-embed-text",
        prompt="This input text doesn't matter because the client is mocked"
    )


def test_embedding_module_raises_connection_error(monkeypatch):
    """
    Tests that a ConnectionError is raised if the Ollama server is down
    when the module is first imported.
    """
    # Make the ollama.Client constructor raise an exception
    monkeypatch.setattr("ollama.Client", MagicMock(side_effect=Exception("connection failed")))

    # We expect a ConnectionError when we try to import the module
    with pytest.raises(ConnectionError, match="Could not connect to Ollama"):
        import importlib
        import ucr_chatbot.api.embedding.embedding
        importlib.reload(ucr_chatbot.api.embedding.embedding)