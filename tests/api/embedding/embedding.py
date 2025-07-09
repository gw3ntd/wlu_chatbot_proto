import pytest
import numpy as np
from typing import Sequence
from unittest.mock import MagicMock

# Assuming your embedding function is in a file like this
from your_project.context_retrieval import embed_text

def test_embed_text_transforms_data_correctly(monkeypatch):
    """
    Tests that embed_text correctly calls the client and transforms
    the output into a list of floats.
    """
    # 1. Create a fake Ollama client
    mock_ollama_client = MagicMock()

    # 2. Define the fake data the client should return.
    # The real client returns a dictionary, so we'll mimic that.
    fake_embedding = [0.1, -0.2, 0.3, 0.4]
    mock_ollama_client.embeddings.return_value = {"embedding": fake_embedding}

    # 3. Use monkeypatch to replace the real client with our fake one
    # This assumes the client is instantiated in your context_retrieval module
    monkeypatch.setattr("your_project.context_retrieval.client", mock_ollama_client)

    # 4. Call the function you want to test
    result = embed_text("This text does not matter because the client is mocked")

    # 5. Assert that the results are correct
    assert isinstance(result, list)
    assert result == fake_embedding
    assert all(isinstance(x, float) for x in result)

    # Bonus: Assert that the underlying client was called correctly
    mock_ollama_client.embeddings.assert_called_once_with(
        "nomic-embed-text:latest", "This text does not matter because the client is mocked"
    )