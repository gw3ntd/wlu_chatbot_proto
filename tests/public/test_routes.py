def test_hello(client):
    response = client.get('/')
    assert "200 OK" == response.status