from flask.testing import FlaskClient
import io
import os
from ucr_chatbot.db.models import upload_folder, Users, engine, Session, ParticipatesIn
from db.helper_functions import *
from unittest.mock import MagicMock
from sqlalchemy import insert, select, delete, inspect

from flask_login import login_user
from werkzeug.security import generate_password_hash

def test_course_selection_ok_response(client: FlaskClient):
    response = client.get('/')
    assert "200 OK" == response.status
    assert "200 OK" == response.status

def test_file_upload(client: FlaskClient, monkeypatch, app):
    # --- Step 1: Add test user to DB ---
    with app.app_context():
        add_new_user("testupload@ucr.edu", "John", "Doe")
        add_user_to_course("testupload@ucr.edu", "John", "Doe", 1, "instructor")

    with client.session_transaction() as session:
        session["_user_id"] = "testupload@ucr.edu" 

    mock_ollama_client = MagicMock()
    fake_embedding = [0.1, -0.2, 0.3, 0.4]
    mock_ollama_client.embeddings.return_value = {"embedding": fake_embedding}
    monkeypatch.setattr("ucr_chatbot.api.embedding.embedding.client", mock_ollama_client)

    data = {"file": (io.BytesIO(b"Test file for CS009A"), "test_file.txt")}
    response = client.post("/course/1/documents", data=data, content_type="multipart/form-data", follow_redirects=True)

    assert response.status_code == 200
    assert b"test_file.txt" in response.data

    file_path = os.path.join(upload_folder, "1", "test_file.txt")
    assert os.path.exists(file_path)
    with open(file_path, "rb") as f:
        assert f.read() == b"Test file for CS009A"
    os.remove(file_path)


def test_file_upload_empty(client: FlaskClient):
    response = client.post("/course/1/documents", data={}, content_type="multipart/form-data")
    assert "302 FOUND" == response.status # Successful redirect


def test_file_upload_no_file(client: FlaskClient):
    data = {}
    data["file"] = (io.BytesIO(b""), "")

    response = client.post("/course/1/documents", data=data, content_type="multipart/form-data")
    assert "302 FOUND" == response.status # Successful redirect


def test_file_upload_invalid_extension(client: FlaskClient, app):
    # create and log in a test user
    with app.app_context():
        add_new_user("testinvalid@ucr.edu", "John", "Doe")
        add_user_to_course("testinvalid@ucr.edu", "John", "Doe", 1, "instructor")

    with client.session_transaction() as sess:
        sess["_user_id"] = "testinvalid@ucr.edu"

    data = {
        "file": (io.BytesIO(b"dog,cat,bird"), "animals.csv")
    }

    response = client.post(
        "/course/1/documents",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True  
    )

    assert response.status_code == 200
    assert b"You can't upload this type of file" in response.data


def test_file_download(client: FlaskClient, monkeypatch, app):
    with app.app_context():
        add_new_user("testdownload@ucr.edu", "John", "Doe")
        add_user_to_course("testdownload@ucr.edu", "John", "Doe", 1, "instructor")

    with client.session_transaction() as sess:
        sess["_user_id"] = "testdownload@ucr.edu"

    mock_ollama_client = MagicMock()
    fake_embedding = [0.1, -0.2, 0.3, 0.4]
    mock_ollama_client.embeddings.return_value = {"embedding": fake_embedding}
    monkeypatch.setattr("ucr_chatbot.api.embedding.embedding.client", mock_ollama_client)

    data = {
        "file": (io.BytesIO(b"Test file for CS009A"), "test_file_download.txt")
    }
    response = client.post(
        "/course/1/documents",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200

    file_path = os.path.join("1", "test_file_download.txt")
    response = client.get(f"/document/{file_path}/download")

    #assert response.status_code == 200
    print(response.data)
    assert response.data == b"Test file for CS009A"

    full_file_path = os.path.join(upload_folder, "1", "test_file_download.txt")
    assert os.path.exists(full_file_path)
    with open(full_file_path, "rb") as f:
        assert f.read() == b"Test file for CS009A"
    
    response = client.get("/course/1/documents")
    assert response.status_code == 200
    os.remove(full_file_path)


def test_file_delete(client: FlaskClient, monkeypatch, app):
    with app.app_context():
        with Session(engine) as session:
            existing_user = session.query(Users).filter_by(email="testdelete@ucr.edu").first()
            if existing_user:
                session.query(ParticipatesIn).filter_by(email="testdelete@ucr.edu").delete()
                session.delete(existing_user)
                session.commit()

            user = Users(
                email="testdelete@ucr.edu",
                first_name="John",
                last_name="Doe",
                password_hash=generate_password_hash("test123"),
            )
            session.add(user)
            session.commit()

            participation = ParticipatesIn(email="testdelete@ucr.edu", course_id=1, role="instructor")
            session.add(participation)
            session.commit()

    with client.session_transaction() as sess:
        sess["_user_id"] = "testdelete@ucr.edu"

    mock_ollama_client = MagicMock()
    fake_embedding = [0.1, -0.2, 0.3, 0.4]
    mock_ollama_client.embeddings.return_value = {"embedding": fake_embedding}
    monkeypatch.setattr("ucr_chatbot.api.embedding.embedding.client", mock_ollama_client)

    data = {"file": (io.BytesIO(b"Test file for CS009A"), "test_file_delete.txt")}
    response = client.post(
        "/course/1/documents",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"test_file_delete.txt" in response.data

    file_path = os.path.join("1", "test_file_delete.txt")

    response = client.post(f"/document/{file_path}/delete", follow_redirects=False)
    assert response.status_code == 302

    full_path = os.path.join(upload_folder, file_path)
    assert os.path.exists(full_path)
    with open(full_path, "rb") as f:
        assert f.read() == b"Test file for CS009A"

    os.remove(full_path)

def test_add_user(client: FlaskClient, app):
    with app.app_context():
        add_new_user("testadd_instructor@ucr.edu", "John", "Doe")
        add_user_to_course("testadd_instructor@ucr.edu", "John", "Doe", 1, "instructor")

    with client.session_transaction() as sess:
        sess["_user_id"] = "testadd_instructor@ucr.edu"

    data = {"email": "testadd@ucr.edu", "fname": "testadd_fname", "lname": "testadd_lname"}
    response = client.post("/course/1/add_user", data=data, content_type="multipart/form-data")
    assert "302 FOUND" == response.status

def test_add_students_from_list(client: FlaskClient, app):
    with app.app_context():
        add_new_user("testaddlist_instructor@ucr.edu", "John", "Doe")
        add_user_to_course("testaddlist_instructor@ucr.edu", "John", "Doe", 1, "instructor")

    with client.session_transaction() as sess:
        sess["_user_id"] = "testaddlist_instructor@ucr.edu"

    csv_data = """Student, SIS User ID
    extra line 1
    extra line 2
    lname1, fname1,s001
    lname2, fname2, s002
    """
    data = {}
    data["file"] = (io.BytesIO(csv_data.encode()), "student_list.csv")

    response = client.post("/course/1/add_from_csv", data=data, content_type="multipart/form-data")
    assert "302 FOUND" == response.status

