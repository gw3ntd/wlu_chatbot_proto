from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session
from wlu_chatbot.db.models import (
    get_engine,
    Conversation,
    Message,
    )
from ..conftest import MockCourse
from .. import authenticate_as

def test_generate_ai_response(mock_course: MockCourse, app: Flask, client: FlaskClient):
    with Session(get_engine()) as sess:
        conv = Conversation(course_id = mock_course.course_id, initiated_by=mock_course.student_email)
        sess.add(conv)
        sess.commit()
        conv_id = conv.id

    authenticate_as(client, mock_course.student_email)

    response = client.post("/messages", json={"conversation_id": conv_id, "body": "hello"})
    assert response.status_code < 400
    
    response = client.post(f"/conversations/{conv_id}/ai-responses")
    assert response.status_code < 400
    assert response.json
    ai_response = response.json["text"]
    assert isinstance(ai_response, str)
    assert len(ai_response) > 0

    with Session(get_engine()) as sess:
        assert sess.query(Message).count() == 2


def test_generate_multiple_ai_response(mock_course: MockCourse, app: Flask, client: FlaskClient):
    with Session(get_engine()) as sess:
        conv = Conversation(course_id = mock_course.course_id, initiated_by=mock_course.student_email)
        sess.add(conv)
        sess.commit()
        conv_id = conv.id

    authenticate_as(client, mock_course.student_email)

    response = client.post("/messages", json={"conversation_id": conv_id, "body": "hello"})
    assert response.status_code < 400
    
    response = client.post(f"/conversations/{conv_id}/ai-responses")
    assert response.status_code < 400

    response = client.post("/messages", json={"conversation_id": conv_id, "body": "hello"})
    assert response.status_code < 400
    
    response = client.post(f"/conversations/{conv_id}/ai-responses")
    assert response.status_code < 400

    response = client.post("/messages", json={"conversation_id": conv_id, "body": "hello"})
    assert response.status_code < 400
    
    response = client.post(f"/conversations/{conv_id}/ai-responses")
    assert response.status_code < 400


    with Session(get_engine()) as sess:
        assert sess.query(Message).count() == 6


def test_cannot_generate_successive_ai_responses(mock_course: MockCourse, app: Flask, client: FlaskClient):
    with Session(get_engine()) as sess:
        conv = Conversation(course_id = mock_course.course_id, initiated_by=mock_course.student_email)
        sess.add(conv)
        sess.commit()
        conv_id = conv.id

    authenticate_as(client, mock_course.student_email)

    response = client.post("/messages", json={"conversation_id": conv_id, "body": "hello"})
    assert response.status_code < 400
    
    response = client.post(f"/conversations/{conv_id}/ai-responses")
    assert response.status_code < 400

    response = client.post(f"/conversations/{conv_id}/ai-responses")
    assert response.status_code >= 400

    response = client.post(f"/conversations/{conv_id}/ai-responses")
    assert response.status_code >= 400

    with Session(get_engine()) as sess:
        assert sess.query(Message).count() == 2