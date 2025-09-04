from flask.testing import FlaskClient
from ..conftest import MockCourse
from .. import authenticate_as

def test_unauthenticated_user_cannot_access_instructor_portal(client: FlaskClient, mock_course: MockCourse):
    response = client.get(f"course/{mock_course.course_id}/documents")
    assert response.status_code >= 300
    assert "upload" not in response.text.lower()

def test_authenticated_student_cannot_access_instructor_portal(client: FlaskClient, mock_course: MockCourse):
    authenticate_as(client, mock_course.student_email)

    response = client.get(f"course/{mock_course.course_id}/documents")
    assert response.status_code >= 400
    assert "upload" not in response.text.lower()


def test_authenticated_instructor_cannot_access_another_instructors_portal(client: FlaskClient, mock_course: MockCourse, mock_course2: MockCourse):
    authenticate_as(client, mock_course2.instructor_email)

    response = client.get(f"course/{mock_course.course_id}/documents")
    assert response.status_code >= 400
    assert "upload" not in response.text.lower()


def test_authenticated_instructor_can_access_his_instructor_portal(client: FlaskClient, mock_course: MockCourse):
    authenticate_as(client, mock_course.instructor_email)

    response = client.get(f"course/{mock_course.course_id}/documents")
    assert response.status_code < 400
    assert "upload" in response.text.lower()
