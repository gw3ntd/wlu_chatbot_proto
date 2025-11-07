from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session
from wlu_chatbot.db.models import (
    get_engine,
    Conversation,
    Limit,
    Message,
    )
from ..conftest import MockCourse
from .. import authenticate_as
import time

def test_cannot_exceed_rate_limit(mock_course: MockCourse, app: Flask, client: FlaskClient):
    with Session(get_engine()) as sess:
        conv = Conversation(course_id = mock_course.course_id, initiated_by=mock_course.student_email)
        sess.add(conv)
        limit = Limit(course_id=mock_course.course_id, maximum_number_of_uses=2, time_span_seconds=5)
        sess.add(limit)
        sess.commit()
        conv_id = conv.id

    authenticate_as(client, mock_course.student_email)

    response = client.post("/messages", json={"conversation_id": conv_id, "body": "test message"})
    assert response.status_code < 400
    
    response = client.post(f"/conversations/{conv_id}/ai-responses")
    assert response.status_code < 400
    response = client.post("/messages", json={"conversation_id": conv_id, "body": "test message"})
    assert response.status_code < 400
    response = client.post(f"/conversations/{conv_id}/ai-responses")
    assert response.status_code < 400
    response = client.post("/messages", json={"conversation_id": conv_id, "body": "test message"})
    assert response.status_code >= 400
    response = client.post(f"/conversations/{conv_id}/ai-responses")
    assert response.status_code >= 400

    with Session(get_engine()) as sess:
        assert sess.query(Message).count() == 4


def test_abidding_by_rate_limit(mock_course: MockCourse, app: Flask, client: FlaskClient):
    with Session(get_engine()) as sess:
        conv = Conversation(course_id = mock_course.course_id, initiated_by=mock_course.student_email)
        sess.add(conv)
        limit = Limit(course_id=mock_course.course_id, maximum_number_of_uses=2, time_span_seconds=2)
        sess.add(limit)
        sess.commit()
        conv_id = conv.id

    authenticate_as(client, mock_course.student_email)

    response = client.post("/messages", json={"conversation_id": conv_id, "body": "test message"})
    assert response.status_code < 400
    
    response = client.post(f"/conversations/{conv_id}/ai-responses")
    assert response.status_code < 400
    response = client.post("/messages", json={"conversation_id": conv_id, "body": "test message"})
    assert response.status_code < 400
    response = client.post(f"/conversations/{conv_id}/ai-responses")
    assert response.status_code < 400

    time.sleep(2)
    response = client.post("/messages", json={"conversation_id": conv_id, "body": "test message"})
    assert response.status_code < 400
    response = client.post(f"/conversations/{conv_id}/ai-responses")
    assert response.status_code < 400

    with Session(get_engine()) as sess:
        assert sess.query(Message).count() == 6
