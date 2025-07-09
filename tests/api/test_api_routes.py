from flask.testing import FlaskClient
def test_generate_ok_response(client: FlaskClient):
    response = client.post('/api/generate', json={"prompt": "Four score and seven years ago" , "conversation_id": 0})
    assert "200 OK" == response.status