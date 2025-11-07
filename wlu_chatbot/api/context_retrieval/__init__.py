"""This module contains functionality for retrieving documents and
other text segments relevant for prompts to the system."""

__all__ = ["retriever"]
from .retriever import Retriever as _Retriever

retriever = _Retriever()
