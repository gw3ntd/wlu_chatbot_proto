from io import BufferedIOBase
from pathlib import Path


class FileParsingError(ValueError):
    """File cannot be parsed."""

    pass


class InvalidFileExtensionError(FileParsingError):
    """Bad file extension"""

    def __init__(self, extension: str):
        self.__init__(f'Cannot interpret file with extension "{extension}"')


def parse_file(path: str) -> str:
    """Parses a file into text.

    :param path: A file path to the file to be parsed.
    :raises InvalidFileExtension: If the input path has an invalid file extension at the end.
    :return: A textual representation of the file.
    """
    extension = Path(path).suffix[1:]
    with open(path, "rb") as f:
        if extension == "pdf":
            return _parse_pdf(f)
        else:
            raise InvalidFileExtensionError(extension)


def _parse_pdf(pdf_file: BufferedIOBase) -> str:
    # Test edit
    return "pdf text"
