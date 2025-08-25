from abc import ABC, abstractmethod
from pathlib import PurePath, Path
from typing import IO
import io

from flask import g

from ucr_chatbot.config import FileStorageMode, app_config


class StorageService(ABC):
    """Controls interactions with file storage backends."""

    @abstractmethod
    def save_file(self, file: IO[bytes], filename: PurePath) -> None | str:
        """Saves a file and returns an Identifier if it has one. Creates any necessary folders to create the file."""

    @abstractmethod
    def delete_file(self, filename: PurePath) -> None:
        """Deletes a file or empty directory."""

    @abstractmethod
    def get_file(self, filename: PurePath) -> IO[bytes]:
        """Gets a file and returns a binary stream."""

    @abstractmethod
    def is_directory(self, path: PurePath) -> bool:
        """Checks if a path is a directory."""

    @abstractmethod
    def list_directory(self, path: PurePath) -> list[PurePath]:
        """Lists the files in a directory."""

    def recursive_delete(self, path: PurePath):
        """Recursively deletes a directory and all its contents."""
        for item in self.list_directory(path):
            self.recursive_delete(item)
        self.delete_file(path)

    def file_exists(self, filename: PurePath) -> bool:
        """Checks if a file exists."""
        if filename == PurePath():
            raise ValueError("Filename cannot be empty")

        return filename in self.list_directory(filename.parent)


class LocalStorage(StorageService):
    """A local filesystem storage service."""

    def __init__(self, storage_path: Path):
        self._storage_path = storage_path
        self._storage_path.mkdir(parents=True, exist_ok=True)

    def save_file(self, file: IO[bytes], filename: PurePath) -> None:  # noqa: D102
        (self._storage_path / filename.parent).mkdir(parents=True, exist_ok=True)
        with open(self._storage_path / filename, "wb") as f:
            f.write(file.read())

    def delete_file(self, filename: PurePath) -> None:  # noqa: D102
        file = self._storage_path / filename
        if file.is_dir():
            file.rmdir()
        else:
            file.unlink()

    def get_file(self, filename: PurePath) -> io.BufferedReader:  # noqa: D102
        return open(self._storage_path / filename, "rb")

    def is_directory(self, path: PurePath) -> bool:  # noqa: D102
        return (self._storage_path / path).is_dir()

    def list_directory(self, path: PurePath) -> list[PurePath]:  # noqa: D102
        full_path = self._storage_path / path
        if not full_path.exists() or not full_path.is_dir():
            return []
        return [
            PurePath(item.relative_to(self._storage_path))
            for item in full_path.iterdir()
        ]


def get_storage_service() -> StorageService:
    """Gets the storage service instance. Must be called from within a request context."""
    if g.get("_storage_service") is None:
        match app_config.FILE_STORAGE_MODE:
            case FileStorageMode.LOCAL:
                g._storage_service = LocalStorage(Path(app_config.FILE_STORAGE_PATH))
    return g._storage_service
