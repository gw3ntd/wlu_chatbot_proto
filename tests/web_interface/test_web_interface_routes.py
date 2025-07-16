from flask.testing import FlaskClient
import io
import os
from ucr_chatbot.web_interface.routes import documents

def test_course_selection_ok_response(client: FlaskClient):
    response = client.get('/')
    assert "200 OK" == response.status


def test_file_upload(client: FlaskClient):
    data = {}
    data["file"] = (io.BytesIO(b"Test file for CS009A"), "test_file.txt")

    response = client.post("/course/91/documents", data=data, content_type="multipart/form-data")

    assert "200 OK" == response.status
    assert b"test_file.txt" in response.data

    app_instance = client.application
    file_path = os.path.join(os.path.join(app_instance.config["UPLOAD_FOLDER"], "CS009A"), "test_file.txt")
    assert os.path.exists(file_path)
    with open(file_path, "rb") as f:
        assert f.read() == b"Test file for CS009A"
    os.remove(file_path)


def test_file_upload_empty(client: FlaskClient):
    response = client.post("/course/91/documents", data={}, content_type="multipart/form-data")
    assert "302 FOUND" == response.status # Successful redirect


def test_file_upload_no_file(client: FlaskClient):
    data = {}
    data["file"] = (io.BytesIO(b""), "")

    response = client.post("/course/91/documents", data=data, content_type="multipart/form-data")
    assert "302 FOUND" == response.status # Successful redirect


def test_file_upload_invalid_extension(client: FlaskClient):
    data = {}
    data["file"] = (io.BytesIO(b"dog,cat,bird"), "animals.csv")

    response = client.post("/course/91/documents", data=data, content_type="multipart/form-data")

    assert "200 OK" == response.status
    assert b"You can't upload this type of file" in response.data


def test_file_download(client: FlaskClient):
    data = {}
    data["file"] = (io.BytesIO(b"Test file for CS009A"), "test_file_download.txt")

    response = client.post("/course/91/documents", data=data, content_type="multipart/form-data")
    assert "200 OK" == response.status

    response = client.get(f"/course/91/documents/uploads/test_file_download.txt")

    assert "200 OK" == response.status
    assert response.data == b"Test file for CS009A"

    app_instance = client.application
    file_path = os.path.join(os.path.join(app_instance.config["UPLOAD_FOLDER"], "CS009A"), "test_file_download.txt")

    assert os.path.exists(file_path)
    with open(file_path, "rb") as f:
        assert f.read() == b"Test file for CS009A"

    response = client.get("/")
    assert "200 OK" == response.status

    os.remove(file_path)


def test_file_delete(client: FlaskClient):
    data = {}
    data["file"] = (io.BytesIO(b"Test file for CS009A"), "test_file_delete.txt")

    response = client.post("/course/91/documents", data=data, content_type="multipart/form-data")
    assert "200 OK" == response.status

    app_instance = client.application
    file_path = os.path.join(os.path.join(app_instance.config["UPLOAD_FOLDER"], "CS009A"), "test_file_delete.txt")

    response = client.post("/course/91/documents/delete/test_file_delete.txt")

    assert file_path in documents
    assert documents[file_path] is False

    assert os.path.exists(file_path)
    with open(file_path, "rb") as f:
        assert f.read() == b"Test file for CS009A"
    os.remove(file_path)
