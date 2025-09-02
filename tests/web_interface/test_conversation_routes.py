from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session
from ucr_chatbot.db.models import get_engine, ParticipatesIn, Users, Conversations
from ..conftest import MockCourse


def  test_no_redirect_to_ula_button_when_no_assistants_added(mock_course: MockCourse, app: Flask, client: FlaskClient):
    with Session(get_engine()) as sess:
        conv = Conversations(course_id = mock_course.course_id, initiated_by=mock_course.student_email)
        sess.add(conv)
        sess.commit()
        conv_id = conv.id

    with client.session_transaction() as session:
        session["_user_id"] = mock_course.student_email
    response = client.get(f"/conversation/{conv_id}")
    assert "redirect to" not in response.text.lower()

def test_not_redirectable_when_no_assistants_added(mock_course: MockCourse, app: Flask, client: FlaskClient):
    with Session(get_engine()) as sess:
        conv = Conversations(course_id = mock_course.course_id, initiated_by=mock_course.student_email)
        sess.add(conv)
        sess.commit()
        conv_id = conv.id

    with client.session_transaction() as session:
        session["_user_id"] = mock_course.student_email

    response = client.post(f"/conversation/{conv_id}/redirect")
    assert response.status_code >= 400

    with Session(get_engine()) as sess:
        conv = sess.query(Conversations).where(Conversations.id == conv_id).first()
        assert conv.redirected == False
        assert conv.resolved == False


def  test_exists_redirect_to_ula_button_when_assistants_added(mock_course: MockCourse, app: Flask, client: FlaskClient):
    with Session(get_engine()) as sess:
        conv = Conversations(course_id = mock_course.course_id, initiated_by=mock_course.student_email)
        sess.add(conv)
        sess.commit()
        conv_id = conv.id

    with Session(get_engine()) as sess:
        assistant = Users(email="assistant@ucr.edu", password_hash="")
        p_in = ParticipatesIn(email=assistant.email, course_id=mock_course.course_id, role="assistant")
        sess.add(p_in)
        sess.add(assistant)
        sess.commit()

    with client.session_transaction() as session:
        session["_user_id"] = mock_course.student_email

    response = client.get(f"/conversation/{conv_id}")
    assert "redirect to" in response.text.lower()

def test_redirectable_when_assistants_added(mock_course: MockCourse, app: Flask, client: FlaskClient):
    with Session(get_engine()) as sess:
        conv = Conversations(course_id = mock_course.course_id, initiated_by=mock_course.student_email)
        sess.add(conv)
        sess.commit()
        conv_id = conv.id

        assistant = Users(email="assistant@ucr.edu", password_hash="")
        p_in = ParticipatesIn(email=assistant.email, course_id=mock_course.course_id, role="assistant")
        sess.add(p_in)
        sess.add(assistant)
        sess.commit()


    with client.session_transaction() as session:
        session["_user_id"] = mock_course.student_email

    response = client.post(f"/conversation/{conv_id}/redirect")
    assert response.status_code < 400

    with Session(get_engine()) as sess:
        conv = sess.query(Conversations).where(Conversations.id == conv_id).first()
        assert conv.redirected == True
        assert conv.resolved == False