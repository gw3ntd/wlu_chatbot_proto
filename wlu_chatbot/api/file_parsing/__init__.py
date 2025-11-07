"""Contains functions for converting files into plain text."""

from .file_parsing import parse_file, FileParsingError

__all__ = ["parse_file", "FileParsingError"]
