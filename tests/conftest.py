import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ucr_chatbot import create_app
from flask import Flask
import pytest

from sqlalchemy import create_engine, String, Column, Integer, DateTime, ForeignKey, Text, insert
from sqlalchemy.orm import declarative_base, mapped_column
from datetime import datetime

from sqlalchemy.orm import sessionmaker

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
    })
    
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db(app):
    db_connect = ""
    password=""
    if (app.config['TESTING']):
        db_connect = f"postgresql+psycopg://postgres:{password}@127.0.0.1:5432/testing_tutor"
    else:
        db_connect = f"postgresql+psycopg://postgres:{password}@127.0.0.1:5432/prod_tutor"
    
    engine = create_engine(db_connect)
    conn = engine.connect()
    yield conn

