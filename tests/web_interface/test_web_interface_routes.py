import io
from pathlib import Path

from flask import Flask
from flask.testing import FlaskClient

from ..conftest import MockCourse

from ucr_chatbot.db.models import get_engine, Session, Users, Documents
from ucr_chatbot.api.file_storage import StorageService


def test_course_selection_ok_response(client: FlaskClient):
    response = client.get('/')
    assert "200 OK" == response.status
    assert "200 OK" == response.status



def test_file_upload(client: FlaskClient, mock_course: MockCourse, storage_service: StorageService):
    with client.session_transaction() as session:
        session["_user_id"] = mock_course.instructor_email

    data = {"file": (io.BytesIO(b"Test file for CS009A"), "test_file.txt")}
    response = client.post(f"/course/{mock_course.course_id}/documents", data=data, content_type="multipart/form-data", follow_redirects=True)

    assert response.status_code == 200
    assert b"test_file.txt" in response.data

    file_path = Path("1",  "test_file.txt")

    with storage_service.get_file(file_path) as f:
        assert f.read() == b"Test file for CS009A"
    storage_service.delete_file(file_path)


def test_file_upload_empty(client: FlaskClient, mock_course: MockCourse):
    with client.session_transaction() as session:
        session["_user_id"] = mock_course.instructor_email
    response = client.post(f"/course/{mock_course.course_id}/documents", data={}, content_type="multipart/form-data")
    assert response.status_code >= 400


def test_file_upload_no_file(client: FlaskClient, mock_course: MockCourse):
    with client.session_transaction() as session:
        session["_user_id"] = mock_course.instructor_email
    data = {}
    data["file"] = (io.BytesIO(b""), "")

    response = client.post(f"/course/{mock_course.course_id}/documents", data=data, content_type="multipart/form-data")
    assert response.status_code >= 400


def test_file_upload_invalid_extension(client: FlaskClient, app: Flask, mock_course: MockCourse):

    with client.session_transaction() as sess:
        sess["_user_id"] = mock_course.instructor_email

    data = {
        "file": (io.BytesIO(b"dog,cat,bird"), "animals.csv")
    }

    response = client.post(
        f"/course/{mock_course.course_id}/documents",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True  
    )


    assert response.status_code >= 400



def test_file_download(client: FlaskClient, app: FlaskClient, mock_course: MockCourse):
    with client.session_transaction() as sess:
        sess["_user_id"] = mock_course.instructor_email

    data = {
        "file": (io.BytesIO(b"Test file for CS009A"), "test_file_download.txt")
    }
    response = client.post(
        f"/course/{mock_course.course_id}/documents",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200

    file_path_rel = str(Path("1") / Path("test_file_download.txt"))
    response = client.get(f"/document/{file_path_rel}/download")

    assert response.data == b"Test file for CS009A"


def test_file_delete(client: FlaskClient, app: Flask, mock_course: MockCourse):

    with client.session_transaction() as sess:
        sess["_user_id"] = mock_course.instructor_email

    data = {"file": (io.BytesIO(b"Test file for CS009A"), "test_file_delete.txt")}
    response = client.post(
        f"/course/{mock_course.course_id}/documents",
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
        with Session(get_engine()) as session:
            document = session.query(Documents).filter_by(file_path=file_path_rel).first()
            assert document is not None
            assert not document.is_active


# TODO Update this test to current routes because they have changed since the test was written.
# def test_chatroom_conversation_flow(client: FlaskClient, mock_course: MockCourse):
#     with client.session_transaction() as sess:
#         sess["_user_id"] = mock_course.student_email

#     init_message = "Hello, I need help with my homework."
#     response = client.post(
#         f"/conversation/new/{mock_course.course_id}/chat",
#         json={"type": "create", "message": init_message},
#         headers={"Accept": "application/json"}
#     )
#     assert response.status_code == 200
#     data = response.get_json()
#     assert "conversationId" in data
#     assert "title" in data
#     conversation_id = data["conversationId"]

#     response = client.post(
#         f"/conversation/{conversation_id}",
#         json={"type": "reply", "message": init_message},
#         headers={"Accept": "application/json"}
#     )
#     assert response.status_code == 200
#     data = response.get_json()
#     assert "reply" in data
#     assert isinstance(data["reply"], str)
#     assert len(data["reply"]) > 0

#     followup_message = "Can you explain recursion?"
#     response = client.post(
#         f"/conversation/{conversation_id}",
#         json={"type": "send", "message": followup_message},
#         headers={"Accept": "application/json"}
#     )
#     assert response.status_code == 200
#     data = response.get_json()
#     assert data["status"] == "200"

#     response = client.post(
#         f"/conversation/{conversation_id}",
#         json={"type": "reply", "message": followup_message},
#         headers={"Accept": "application/json"}
#     )
#     assert response.status_code == 200
#     data = response.get_json()
#     assert "reply" in data
#     assert isinstance(data["reply"], str)
#     assert len(data["reply"]) > 0

def test_add_participant(client: FlaskClient, app: Flask, mock_course: MockCourse):
    
    with client.session_transaction() as sess:
        sess["_user_id"] = mock_course.instructor_email

    data = {"email": "testadd@ucr.edu", "fname": "testadd_fname", "lname": "testadd_lname", "role": "student"}
    response = client.post(f"/course/{mock_course.course_id}/add_participant", data=data, content_type="multipart/form-data")
    assert response.status_code < 400

    with Session(get_engine()) as session:
        user = session.query(Users).filter_by(email="testadd@ucr.edu").first()
        assert user is not None
        for participation in user.participates_in:
            assert participation.course_id == mock_course.course_id
            assert participation.role == "student"

def test_add_students_from_list(client: FlaskClient, app: Flask, mock_course: MockCourse):

    with client.session_transaction() as sess:
        sess["_user_id"] = mock_course.instructor_email

    csv_data = """Student,SIS User ID
This is row 1 and will be skipped
This is row 2 and will be skipped
"lname1, fname1",s001
"lname2, fname2",s002
"""
    data = {}
    data["file"] = (io.BytesIO(csv_data.encode()), "student_list.csv")

    response = client.post(f"/course/{mock_course.course_id}/add_from_csv", data=data, content_type="multipart/form-data")

    assert response.status_code < 400

    with Session(get_engine()) as session:
        user1 = session.query(Users).filter_by(email="s001@ucr.edu").first()
        user2 = session.query(Users).filter_by(email="s002@ucr.edu").first()
        assert user1 is not None
        assert user2 is not None
        for user in [user1, user2]:
            for participation in user.participates_in:
                assert participation.course_id == mock_course.course_id
                assert participation.role == "student"


def test_generate_summary(client: FlaskClient, mock_course: MockCourse):

    with client.session_transaction() as sess:
        sess["_user_id"] = mock_course.instructor_email
    

    response = client.post(
    f"/course/{mock_course.course_id}/generate_summary",
    data={"start_date": "2025-06-01", "end_date": "2025-07-31"},
    follow_redirects=True
    )
    llm_summary = response.data.decode()
    assert response.status_code == 200
    assert "Interaction Report" in llm_summary

    
    