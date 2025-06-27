def test_course_selection_ok_response(client):
    response = client.get('/')
    assert "200 OK" == response.status