from ucr_chatbot.api.language_model import get_response_from_prompt, stream_response_from_prompt
from typing import Iterable

def test_get_response_from_prompt_return_type():
    assert isinstance(get_response_from_prompt("Where did you come from?"), str)

def test_stream_response_from_prompt_return_type():
    stream = stream_response_from_prompt("Where did you come from?")
    assert isinstance(stream, Iterable)
    for s in stream:
        assert isinstance(s, str)