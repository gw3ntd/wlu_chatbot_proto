from flask.testing import FlaskClient
import io
import os
from ucr_chatbot.db.models import upload_folder
from db.helper_functions import *
from unittest.mock import MagicMock

def test_course_selection_ok_response(client: FlaskClient):
    response = client.get('/')
    assert "200 OK" == response.status
    assert b"<h1>ScotGPT</h1>" in response.data

def test_new_conversation_ok_response(client: FlaskClient):
    response = client.get('/conversation/new/10/chat')
    assert "200 OK" == response.status
    assert b"<h2>CONVERSATIONS</h2>" in response.data

def test_conversation_ok_response(client: FlaskClient):
    response = client.get('/conversation/10')
    assert "200 OK" == response.status
    assert b"<h2>CONVERSATIONS</h2>" in response.data