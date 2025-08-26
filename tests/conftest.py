import sys
from pathlib import Path, PurePath
import pytest
from flask import Flask
from ucr_chatbot import create_app
from ucr_chatbot.db.models import get_engine, base
from ucr_chatbot.api.file_storage import get_storage_service
from ucr_chatbot.config import LLMMode, FileStorageMode

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

@pytest.fixture(scope="function")
def app():
    app = create_app({
        "TESTING": True,
        "FILE_STORAGE_MODE": FileStorageMode.LOCAL,
        "FILE_STORAGE_PATH": "test_storage",
        "REQUIRE_OAUTH": False,
        "LLM_MODE": LLMMode.TESTING
    })
    app.template_folder = str(Path(__file__).resolve().parent.parent / 'ucr_chatbot' / 'templates')

    with app.app_context():
        base.metadata.create_all(get_engine())
        yield app
        base.metadata.drop_all(get_engine())
        get_storage_service().recursive_delete(PurePath(""))

@pytest.fixture
def client(app: Flask):
    return app.test_client()

@pytest.fixture
def storage_service(app: Flask):
    """
    A fixture to directly access the configured StorageService instance.
    """
    yield get_storage_service()


@pytest.fixture
def db(app: Flask):
    connection = get_engine().connect()
    yield connection
    connection.close()
