"""This module contains functionality for sending prompts to a language model
and for receiving a responses therefrom."""

__all__ = ["get_response_from_prompt", "stream_response_from_prompt"]
from .response import get_response_from_prompt, stream_response_from_prompt
