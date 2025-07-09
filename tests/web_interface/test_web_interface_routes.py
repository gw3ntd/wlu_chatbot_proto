from flask.testing import FlaskClient

def test_course_selection_ok_response(client: FlaskClient):
    response = client.get('/')
    assert "200 OK" == response.status