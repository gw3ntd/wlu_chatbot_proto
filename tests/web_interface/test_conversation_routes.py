from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session
from wlu_chatbot.db.models import (
    get_engine,
    ParticipatesIn,
    User,
    Conversation,
    ConversationState,
    ConsentForm,
    Consent
    )
from ..conftest import MockCourse
from .. import authenticate_as


def  test_no_redirect_to_ula_button_when_no_assistants_added(mock_course: MockCourse, app: Flask, client: FlaskClient):
    with Session(get_engine()) as sess:
        conv = Conversation(course_id = mock_course.course_id, initiated_by=mock_course.student_email)
        sess.add(conv)
        sess.commit()
        conv_id = conv.id

    with client.session_transaction() as session:
        session["_user_id"] = mock_course.student_email
    response = client.get(f"/conversations/{conv_id}")
    assert response.status_code < 400
    assert "redirect to" not in response.text.lower()
    assert "send" in response.text.lower()

def test_not_redirectable_when_no_assistants_added(mock_course: MockCourse, app: Flask, client: FlaskClient):
    with Session(get_engine()) as sess:
        conv = Conversation(course_id = mock_course.course_id, initiated_by=mock_course.student_email)
        sess.add(conv)
        sess.commit()
        conv_id = conv.id

    with client.session_transaction() as session:
        session["_user_id"] = mock_course.student_email

    response = client.patch(f"/conversations/{conv_id}", json={"state": "REDIRECTED"})
    assert response.status_code >= 400

    with Session(get_engine()) as sess:
        conv = sess.query(Conversation).where(Conversation.id == conv_id).first()
        assert conv.state == ConversationState.CHATBOT


def  test_exists_redirect_to_ula_button_when_assistants_added(mock_course: MockCourse, app: Flask, client: FlaskClient):
    with Session(get_engine()) as sess:
        conv = Conversation(course_id = mock_course.course_id, initiated_by=mock_course.student_email)
        sess.add(conv)
        sess.commit()
        conv_id = conv.id

    with Session(get_engine()) as sess:
        assistant = User(email="assistant@westliberty.edu", password_hash="")
        p_in = ParticipatesIn(email=assistant.email, course_id=mock_course.course_id, role="assistant")
        sess.add(p_in)
        sess.add(assistant)
        sess.commit()

    with client.session_transaction() as session:
        session["_user_id"] = mock_course.student_email

    response = client.get(f"/conversations/{conv_id}")
    assert response.status_code < 400
    assert "redirect to" in response.text.lower()

def test_redirectable_when_assistant_added(mock_course: MockCourse, app: Flask, client: FlaskClient):
    with Session(get_engine()) as sess:
        conv = Conversation(course_id = mock_course.course_id, initiated_by=mock_course.student_email)
        sess.add(conv)
        sess.commit()
        conv_id = conv.id

        assistant = User(email="assistant@westliberty.edu", password_hash="")
        p_in = ParticipatesIn(email=assistant.email, course_id=mock_course.course_id, role="assistant")
        sess.add(p_in)
        sess.add(assistant)
        sess.commit()


    with client.session_transaction() as session:
        session["_user_id"] = mock_course.student_email

    response = client.patch(f"/conversations/{conv_id}", json={"state": "REDIRECTED"})
    assert response.status_code < 400

    with Session(get_engine()) as sess:
        conv = sess.query(Conversation).where(Conversation.id == conv_id).first()
        assert conv.state == ConversationState.REDIRECTED


def test_conversation_redirects_to_consent_form_when_not_consented(mock_course: MockCourse, app: Flask, client: FlaskClient):

    with Session(get_engine()) as sess:
        consent_form = ConsentForm(course_id=mock_course.course_id, body="test consent body", title="test consent title")
        sess.add(consent_form)
        sess.commit()

    authenticate_as(client, mock_course.student_email)
    response = client.get(f"/conversations/new?course_id={mock_course.course_id}", follow_redirects=True)
    assert response.status_code < 400, response.text
    assert "test consent body" in response.text.lower()


def test_conversation_visitable_when_consent_form_agreed(mock_course: MockCourse, app: Flask, client: FlaskClient):

    with Session(get_engine()) as sess:
        consent_form = ConsentForm(course_id=mock_course.course_id, body="test consent body", title="test consent title")
        sess.add(consent_form)
        sess.commit()
        sess.add(Consent(user_email=mock_course.student_email, consent_form_id=consent_form.id))
        sess.commit()    

    authenticate_as(client, mock_course.student_email)

    response = client.get(f"/conversations/new?course_id={mock_course.course_id}", follow_redirects=True)

    assert response.status_code < 400
    assert "test consent body" not in response.text.lower()
    assert "new conversation" in response.text.lower()
    