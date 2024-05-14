import unittest.mock
from http import HTTPStatus

from test_api.conftest import DEFAULT_ACCESS_TOKEN, REQUEST_ACCESS_URI, login


def test_request_access(client):
    login(client, 'foo')

    with unittest.mock.patch('dynamo.user.get_edl_profile') as mock_get_edl_profile:
        mock_get_edl_profile.return_value = {'email_address': 'foo@example.com'}
        response = client.get(REQUEST_ACCESS_URI)
        mock_get_edl_profile.assert_called_once_with('foo', DEFAULT_ACCESS_TOKEN)

    assert response.status_code == HTTPStatus.OK
    assert b'Request Access to ASF On Demand Processing' in response.data
    assert b'<b>Username:</b> foo' in response.data
    assert b'<b>Email Address:</b> foo@example.com' in response.data
