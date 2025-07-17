from flask.testing import FlaskClient
import io
import os
from ucr_chatbot.db.models import upload_folder
from db.helper_functions import *
from unittest.mock import MagicMock

def test_course_selection_ok_response(client: FlaskClient):
    response = client.get('/')
    assert "200 OK" == response.status



def test_file_upload(client: FlaskClient, monkeypatch):
    # delete_uploads_folder()
    # clear_db()
    # initialize_db()
    # add_courses()

    mock_ollama_client = MagicMock()
    fake_embedding = [0.1, -0.2, 0.3, 0.4]
    mock_ollama_client.embeddings.return_value = {"embedding": fake_embedding}
    monkeypatch.setattr("ucr_chatbot.api.embedding.embedding.client", mock_ollama_client)

    data = {}
    data["file"] = (io.BytesIO(b"Test file for CS009A"), "test_file.txt")

    response = client.post("/course/1/documents", data=data, content_type="multipart/form-data")

    assert "200 OK" == response.status
    assert b"test_file.txt" in response.data

    app_instance = client.application
    file_path = os.path.join(os.path.join(upload_folder, "1"), "test_file.txt")
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


def test_file_upload_invalid_extension(client: FlaskClient):
    data = {}
    data["file"] = (io.BytesIO(b"dog,cat,bird"), "animals.csv")

    response = client.post("/course/1/documents", data=data, content_type="multipart/form-data")

    assert "200 OK" == response.status
    assert b"You can't upload this type of file" in response.data


def test_file_download(client: FlaskClient, monkeypatch):
    mock_ollama_client = MagicMock()
    fake_embedding = [0.1, -0.2, 0.3, 0.4]
    mock_ollama_client.embeddings.return_value = {"embedding": fake_embedding}
    monkeypatch.setattr("ucr_chatbot.api.embedding.embedding.client", mock_ollama_client)

    data = {}
    data["file"] = (io.BytesIO(b"Test file for CS009A"), "test_file_download.txt")


    response = client.post("/course/1/documents", data=data, content_type="multipart/form-data")
    assert "200 OK" == response.status

    file_path = os.path.join("1", "test_file_download.txt")
    response = client.get(f"/document/{file_path}/download")

    assert "200 OK" == response.status
    assert response.data == b"Test file for CS009A"

    file_path = os.path.join(upload_folder, file_path)
    assert os.path.exists(file_path)
    with open(file_path, "rb") as f:
        assert f.read() == b"Test file for CS009A"

    response = client.get("/")
    assert "200 OK" == response.status

    os.remove(os.path.join(upload_folder,file_path))


def test_file_delete(client: FlaskClient, monkeypatch):
    mock_ollama_client = MagicMock()
    fake_embedding = [0.1, -0.2, 0.3, 0.4]
    mock_ollama_client.embeddings.return_value = {"embedding": fake_embedding}
    monkeypatch.setattr("ucr_chatbot.api.embedding.embedding.client", mock_ollama_client)

    data = {}
    data["file"] = (io.BytesIO(b"Test file for CS009A"), "test_file_delete.txt")

    response = client.post("/course/1/documents", data=data, content_type="multipart/form-data")
    assert "200 OK" == response.status

    file_path = os.path.join("1", "test_file_delete.txt")

    response = client.post(f"document/{file_path}/delete")

    assert "302 FOUND" == response.status

    full_path = os.path.join(upload_folder,file_path)
    assert os.path.exists(full_path)
    with open(full_path, "rb") as f:
        assert f.read() == b"Test file for CS009A"
    os.remove(full_path)
