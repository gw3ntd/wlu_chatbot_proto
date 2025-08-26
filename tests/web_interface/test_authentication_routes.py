from flask import Flask
from flask.testing import FlaskClient
import pytest

from ucr_chatbot.db.models import Session, Users, get_engine

def test_login(client: FlaskClient, app):
    with Session(get_engine()) as db_session:
        user = Users(email="test@example.com", first_name="test", last_name="user")
        user.set_password("password")
        db_session.add(user)
        db_session.commit()

    response = client.post("/login", data={
        "email": "test@example.com",
        "password": "password"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "select a course" in str(response.data).lower()


def test_logout(client: FlaskClient):
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert "login" in str(response.data).lower()


@pytest.fixture
def oauth_required_app(app: Flask):
    app.config["REQUIRE_OAUTH"] = True
    return app


@pytest.fixture
def oauth_required_client(oauth_required_app: Flask):
    return oauth_required_app.test_client()

def test_non_oauth_login_with_oauth_required(oauth_required_client: FlaskClient, app: Flask):

    with Session(get_engine()) as db_session:
        user = Users(email="test@test.com", first_name="test", last_name="user")
        user.set_password("password")
        db_session.add(user)
        db_session.commit()

    response = oauth_required_client.post("/login", data={
        "email": "test@test.com",
        "password": "password"
    }, follow_redirects=True)
    assert response.status_code >= 400


def test_normal_login_not_visible_when_oauth_required(oauth_required_client: FlaskClient):
    response = oauth_required_client.get("/")
    assert "<form" not in str(response.data).lower()

def test_oauth_login_visible_when_oauth_required(oauth_required_client: FlaskClient):
    response = oauth_required_client.get("/")
    assert "login with google" in str(response.data).lower()

