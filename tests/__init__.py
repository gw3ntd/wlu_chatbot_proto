from flask.testing import FlaskClient
def authenticate_as(client: FlaskClient, email: str):
    with client.session_transaction() as sess:
        sess["_user_id"] = email