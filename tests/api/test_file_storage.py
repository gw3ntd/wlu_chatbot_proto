from pathlib import PurePath, Path
import io

import pytest

from ucr_chatbot.api.file_storage import LocalStorage, StorageService

@pytest.fixture(scope="function")
def local_storage_service():
    """Provides a clean StorageService for each test."""
    storage_path = Path("test_local_storage")
    service = LocalStorage(storage_path)

    yield service

    def delete(path: Path):
        if path.is_dir():
            for child in path.iterdir():
                delete(child)
            path.rmdir()
        else:
            path.unlink()

    if storage_path.exists():
        delete(storage_path)

@pytest.fixture(params=[local_storage_service])
def storage_service(request: pytest.FixtureRequest):
    return request.getfixturevalue(request.param.__name__)

def test_save_file_and_get_file(storage_service: StorageService):
    
    storage_service.save_file(io.BytesIO(b"Test content 1"), PurePath("test1.txt"))
    storage_service.save_file(io.BytesIO(b"Test content 2"), PurePath("test2.txt"))

    with storage_service.get_file(PurePath("test1.txt")) as f:
        content = f.read()
        assert content == b"Test content 1"

    with storage_service.get_file(PurePath("test2.txt")) as f:
        content = f.read()
        assert content == b"Test content 2"


def test_file_exists(storage_service: StorageService):

    assert not storage_service.file_exists(PurePath("test.txt"))
    storage_service.save_file(io.BytesIO(b"Test content"), PurePath("test.txt"))
    assert storage_service.file_exists(PurePath("test.txt"))
    assert not storage_service.file_exists(PurePath("non_existent.txt"))


def test_save_file_and_get_file_with_path(storage_service: StorageService):
    
    storage_service.save_file(io.BytesIO(b"Test content 1"), PurePath("1/test1.txt"))
    storage_service.save_file(io.BytesIO(b"Test content 2"), PurePath("1/test2.txt"))

    with storage_service.get_file(PurePath("1/test1.txt")) as f:
        content = f.read()
        assert content == b"Test content 1"

    with storage_service.get_file(PurePath("1/test2.txt")) as f:
        content = f.read()
        assert content == b"Test content 2"

def test_delete_file(storage_service: StorageService):

    storage_service.save_file(io.BytesIO(b"Test content"), PurePath("test.txt"))
    storage_service.delete_file(PurePath("test.txt"))

    pytest.raises(FileNotFoundError, 
        lambda: storage_service.get_file(PurePath("test.txt")))
    
def test_list_directory(storage_service: StorageService):

    storage_service.save_file(io.BytesIO(b"Test content"), PurePath("test.txt"))
    storage_service.save_file(io.BytesIO(b"Another file"), PurePath("another.txt"))

    storage_service.save_file(io.BytesIO(b"Test content"), PurePath("1/test.txt"))
    storage_service.save_file(io.BytesIO(b"Another file"), PurePath("1/another.txt"))

    files = storage_service.list_directory(PurePath(""))
    assert set(files) == {PurePath("test.txt"), PurePath("another.txt"), PurePath("1")}

    files = storage_service.list_directory(PurePath("1"))
    assert set(files) == {PurePath("1/test.txt"), PurePath("1/another.txt")}


def test_recursive_delete(storage_service: StorageService):

    storage_service.save_file(io.BytesIO(b"Test content"), PurePath("test.txt"))
    storage_service.save_file(io.BytesIO(b"Another file"), PurePath("another.txt"))

    storage_service.save_file(io.BytesIO(b"Test content"), PurePath("1/test.txt"))
    storage_service.save_file(io.BytesIO(b"Another file"), PurePath("1/another.txt"))

    storage_service.recursive_delete(PurePath("1"))

    assert len(storage_service.list_directory(PurePath())) == 2
    assert len(storage_service.list_directory(PurePath("1"))) == 0

    storage_service.save_file(io.BytesIO(b"Test content"), PurePath("1/test.txt"))
    storage_service.save_file(io.BytesIO(b"Another file"), PurePath("1/another.txt"))

    storage_service.recursive_delete(PurePath())

    assert len(storage_service.list_directory(PurePath())) == 0

def test_get_file_in_directory(storage_service: StorageService):

    storage_service.save_file(io.BytesIO(b"Test content"), PurePath("1/test.txt"))

    with storage_service.get_file(PurePath("1/test.txt")) as f:
        content = f.read()
        assert content == b"Test content"

def test_delete_file_in_directory(storage_service: StorageService):

    storage_service.save_file(io.BytesIO(b"Test content"), PurePath("1/test.txt"))
    storage_service.delete_file(PurePath("1/test.txt"))

    pytest.raises(FileNotFoundError,
        lambda: storage_service.get_file(PurePath("1/test.txt")))
