import sys
from pathlib import Path
import pytest
from flask import Flask

from ucr_chatbot import create_app
from ucr_chatbot.db.models import engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
    })
    app.template_folder = str(Path(__file__).resolve().parent.parent / 'ucr_chatbot' / 'templates')
    yield app


@pytest.fixture
def client(app: Flask):
    return app.test_client()


@pytest.fixture
def runner(app: Flask):
    return app.test_cli_runner()


@pytest.fixture
def db():
    connection = engine.connect()
    yield connection
    connection.close()


