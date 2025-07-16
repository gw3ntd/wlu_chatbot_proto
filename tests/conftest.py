import sys
import os
import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection
from typing import Generator
from ucr_chatbot import create_app
from dotenv import load_dotenv
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
    })
    yield app


@pytest.fixture
def client(app: Flask):
    return app.test_client()


@pytest.fixture
def runner(app: Flask):
    return app.test_cli_runner()


@pytest.fixture
def db(app: Flask):
    
    load_dotenv()
    password = os.getenv("DB_PASSWORD")
    db_connect = ""
    if app.config['TESTING']:
        db_connect = f"postgresql+psycopg://postgres:{password}@127.0.0.1:5432/testing_tutor"
    else:
        db_connect = f"postgresql+psycopg://postgres:{password}@127.0.0.1:5432/prod_tutor"

    engine = create_engine(db_connect)
    conn = engine.connect()
    yield conn