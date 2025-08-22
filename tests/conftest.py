import sys
from pathlib import Path
import pytest
from flask import Flask
from typing import cast
from ucr_chatbot import create_app
from ucr_chatbot.db.models import engine
from ucr_chatbot.api.file_storage import LocalStorage

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

@pytest.fixture(scope="function")
def app(tmp_path: Path):
    app = create_app({
        'TESTING': True,
        'FILE_STORAGE_MODE': 'local',
        'FILE_STORAGE': LocalStorage(tmp_path)
    })
    app.template_folder = str(Path(__file__).resolve().parent.parent / 'ucr_chatbot' / 'templates')
    yield app


@pytest.fixture
def client(app: Flask):
    return app.test_client()

@pytest.fixture
def storage_service(app: Flask):
    """
    A fixture to directly access the configured StorageService instance.
    """
    return cast(LocalStorage, app.config['FILE_STORAGE'])

@pytest.fixture
def runner(app: Flask):
    return app.test_cli_runner()


@pytest.fixture
def db():
    connection = engine.connect()
    yield connection
    connection.close()
