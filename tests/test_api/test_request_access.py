from http import HTTPStatus

from test_api.conftest import REQUEST_ACCESS_URI, login


def test_request_access(client):
    login(client, 'foo')

    response = client.get(REQUEST_ACCESS_URI)
    assert response.status_code == HTTPStatus.OK
    assert b'TODO: intro text' in response.data
