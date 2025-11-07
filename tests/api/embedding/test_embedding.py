from wlu_chatbot.api.embedding.embedding import embed_text

def test_embed_text_success(app):
    """
    Tests that embed_text correctly calls the client and returns a list of floats.
    """
    result = embed_text("This input text doesn't matter because the client is mocked")
    assert isinstance(result, list)
    assert all(isinstance(x, float) for x in result)
