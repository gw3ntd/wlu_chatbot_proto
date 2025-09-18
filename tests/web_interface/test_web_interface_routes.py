import io
from pathlib import Path

from flask.testing import FlaskClient

from ..conftest import MockCourse

from ucr_chatbot.db.models import get_engine, Session, User
from ucr_chatbot.api.file_storage import StorageService


def test_course_selection_ok_response(client: FlaskClient):
    response = client.get('/')
    assert "200 OK" == response.status
    assert "200 OK" == response.status


def test_add_participant(client: FlaskClient, mock_course: MockCourse):
    
    with client.session_transaction() as sess:
        sess["_user_id"] = mock_course.instructor_email

    data = {"email": "testadd@ucr.edu", "course_id": mock_course.course_id, "role": "student"}
    response = client.post(f"/participates_ins", data=data)
    assert response.status_code < 400

    with Session(get_engine()) as session:
        user = session.query(User).filter_by(email="testadd@ucr.edu").first()
        assert user is not None
        for participation in user.participates_in:
            assert participation.course_id == mock_course.course_id
            assert participation.role == "student"



def test_file_upload(client: FlaskClient, mock_course: MockCourse, storage_service: StorageService):
    with client.session_transaction() as session:
        session["_user_id"] = mock_course.instructor_email

    data = {"file": (io.BytesIO(b"Test file for CS009A"), "test_file.txt"), "course_id": mock_course.course_id} 
    response = client.post(f"/documents", data=data, content_type="multipart/form-data", follow_redirects=True, headers={"Referer": f"/courses/{mock_course.course_id}/instructor-portal"})

    assert response.status_code < 400
    assert b"test_file.txt" in response.data

    file_path = Path("1",  "test_file.txt")

    with storage_service.get_file(file_path) as f:
        assert f.read() == b"Test file for CS009A"

def test_invalid_file_extension_does_not_upload(client: FlaskClient, mock_course: MockCourse, storage_service: StorageService):
    with client.session_transaction() as session:
        session["_user_id"] = mock_course.instructor_email

    data = {"file": (io.BytesIO(b"Test file for CS009A"), "test_file.ext"), "course_id": mock_course.course_id} 
    response = client.post(f"/documents", data=data, content_type="multipart/form-data", follow_redirects=True, headers={"Referer": f"/courses/{mock_course.course_id}/instructor-portal"})

    assert response.status_code >= 400
    assert b"test_file.ext" not in response.data

    file_path = Path("1",  "test_file.ext")

    assert not storage_service.file_exists(file_path)


def test_generate_summary(client: FlaskClient, mock_course: MockCourse):

    with client.session_transaction() as sess:
        sess["_user_id"] = mock_course.instructor_email
    

    response = client.post(
    f"/courses/{mock_course.course_id}/summaries",
    data={"start_date": "2025-06-01", "end_date": "2025-07-31"},
    follow_redirects=True
    )
    llm_summary = response.data.decode()
    assert response.status_code == 200
    assert "Interaction Report" in llm_summary

    
    