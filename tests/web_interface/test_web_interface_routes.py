from flask.testing import FlaskClient
import io
import os
import sys
from pathlib import Path
from ucr_chatbot.db.models import engine, Session
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db.helper_functions import *
from unittest.mock import MagicMock

from ucr_chatbot.config import Config

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
    fake_embedding = [i for i in range(100)]
    mock_ollama_client.embeddings.return_value = {"embedding": fake_embedding}
    monkeypatch.setattr("ucr_chatbot.api.embedding.embedding.client", mock_ollama_client)

    data = {"file": (io.BytesIO(b"Test file for CS009A"), "test_file.txt")}
    response = client.post("/course/1/documents", data=data, content_type="multipart/form-data", follow_redirects=True)

    assert response.status_code == 200
    assert b"test_file.txt" in response.data

    app_instance = client.application
    file_path = Path(Config.FILE_STORAGE_PATH) / "1" / "test_file.txt"
    assert file_path.exists()
    with file_path.open("rb") as f:
        assert f.read() == b"Test file for CS009A"
    file_path.unlink()


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



def test_file_download(client: FlaskClient, monkeypatch, app):
    with app.app_context():
        add_new_user("testdownload@ucr.edu", "John", "Doe")
        add_user_to_course("testdownload@ucr.edu", "John", "Doe", 1, "instructor")

    with client.session_transaction() as sess:
        sess["_user_id"] = "testdownload@ucr.edu"

    mock_ollama_client = MagicMock()
    fake_embedding = [i for i in range(100)]
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

    file_path_rel = str(Path("1") / Path("test_file_download.txt"))
    response = client.get(f"/document/{file_path_rel}/download")

    #assert response.status_code == 200
    print(response.data)
    assert response.data == b"Test file for CS009A"

    file_path_abs = Path(Config.FILE_STORAGE_PATH) / file_path_rel
    assert file_path_abs.exists()
    with file_path_abs.open("rb") as f:

        assert f.read() == b"Test file for CS009A"
    
    response = client.get("/course/1/documents")
    assert response.status_code == 200
    os.remove(str(file_path_abs))


def test_file_delete(client: FlaskClient, monkeypatch, app):
    with app.app_context():
        add_new_user("testdelete@ucr.edu", "John", "Doe")
        add_user_to_course("testdelete@ucr.edu", "John", "Doe", 1, "instructor")

    with client.session_transaction() as sess:
        sess["_user_id"] = "testdelete@ucr.edu"

    mock_ollama_client = MagicMock()
    fake_embedding = [i for i in range(100)]
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

    file_path_rel = str(Path("1") / Path("test_file_delete.txt"))
    response = client.post(f"/document/{file_path_rel}/delete")

    assert response.status_code == 302

    with app.app_context():
        with Session(engine) as session:
            document = session.query(Documents).filter_by(file_path=file_path_rel).first()
            assert document is not None
            assert not document.is_active

def test_chatroom_conversation_flow(client: FlaskClient, app):
    with app.app_context():

        add_new_user("testconversation@ucr.edu", "Test", "User")
        add_user_to_course("testconversatio@ucr.edu", "Test", "User", 1, "student")

    with client.session_transaction() as sess:
        sess["_user_id"] = "testconversation@ucr.edu"

    course_id = 1
    init_message = "Hello, I need help with my homework."
    response = client.post(
        f"/conversation/new/{course_id}/chat",
        json={"type": "create", "message": init_message},
        headers={"Accept": "application/json"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "conversationId" in data
    conversation_id = data["conversationId"]

    response = client.post(
        f"/conversation/{conversation_id}",
        json={"type": "reply", "message": init_message},
        headers={"Accept": "application/json"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "reply" in data
    assert isinstance(data["reply"], str)
    assert len(data["reply"]) > 0

    followup_message = "Can you explain recursion?"
    response = client.post(
        f"/conversation/{conversation_id}",
        json={"type": "send", "message": followup_message},
        headers={"Accept": "application/json"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "200"

    response = client.post(
        f"/conversation/{conversation_id}",
        json={"type": "reply", "message": followup_message},
        headers={"Accept": "application/json"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "reply" in data
    assert isinstance(data["reply"], str)
    assert len(data["reply"]) > 0

def test_add_user(client: FlaskClient, app):
    with app.app_context():
        add_new_user("testadd_instructor@ucr.edu", "John", "Doe")
        add_user_to_course("testadd_instructor@ucr.edu", "John", "Doe", 1, "instructor")

    with client.session_transaction() as sess:
        sess["_user_id"] = "testadd_instructor@ucr.edu"

    data = {"email": "testadd@ucr.edu", "fname": "testadd_fname", "lname": "testadd_lname", "role": "student"}
    response = client.post("/course/1/add_student", data=data, content_type="multipart/form-data")
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


def test_generate_summary(client: FlaskClient, monkeypatch, app):
    with app.app_context():
        add_new_user("testsum@ucr.edu", "John", "Doe")
        add_user_to_course("testsum@ucr.edu", "John", "Doe", 1, "instructor")

    with client.session_transaction() as sess:
        sess["_user_id"] = "testsum@ucr.edu"
    
    monkeypatch.setattr(
        "ucr_chatbot.web_interface.routes.response_client.get_response",
        MagicMock(return_value="summary of course conversations")
    )

    response = client.post(
    "/course/1/generate_summary",
    data={"start_date": "2025-06-01", "end_date": "2025-07-31"},
    follow_redirects=True
    )
    llm_summary = response.data.decode()
    assert response.status_code == 200
    assert "summary of course conversations" in llm_summary

    
    