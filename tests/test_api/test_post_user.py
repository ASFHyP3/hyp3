import unittest.mock
from decimal import Decimal
from http import HTTPStatus

from test_api.conftest import DEFAULT_ACCESS_TOKEN, USER_URI, login

from dynamo.user import APPLICATION_APPROVED, APPLICATION_NOT_STARTED, APPLICATION_PENDING, APPLICATION_REJECTED


def test_post_user(client, tables):
    login(client, 'foo')
    with unittest.mock.patch('dynamo.user._get_edl_profile') as mock_get_edl_profile:
        mock_get_edl_profile.return_value = {}
        response = client.post(USER_URI, data={'use_case': 'I want data.'})
        mock_get_edl_profile.assert_called_once_with('foo', DEFAULT_ACCESS_TOKEN)

    assert response.status_code == HTTPStatus.OK
    assert response.data == b'<p>Application for <code>foo</code> was successfully submitted.</p>'


def test_post_user_not_started(client, tables):
    tables.users_table.put_item(
        Item={
            'user_id': 'foo',
            'remaining_credits': Decimal(0),
            'application_status': APPLICATION_NOT_STARTED,
        }
    )

    login(client, 'foo')
    with unittest.mock.patch('dynamo.user._get_edl_profile') as mock_get_edl_profile:
        mock_get_edl_profile.return_value = {}
        response = client.post(USER_URI, data={'use_case': 'I want data.'})
        mock_get_edl_profile.assert_called_once_with('foo', DEFAULT_ACCESS_TOKEN)

    assert response.status_code == HTTPStatus.OK
    assert response.data == b'<p>Application for <code>foo</code> was successfully submitted.</p>'


def test_post_user_pending(client, tables):
    tables.users_table.put_item(
        Item={
            'user_id': 'foo',
            'remaining_credits': Decimal(0),
            'application_status': APPLICATION_PENDING,
        }
    )

    login(client, 'foo')
    response = client.post(USER_URI, data={'use_case': 'I want data.'})

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert b'is pending review' in response.data


def test_post_user_rejected(client, tables):
    tables.users_table.put_item(
        Item={
            'user_id': 'foo',
            'remaining_credits': Decimal(0),
            'application_status': APPLICATION_REJECTED,
        }
    )

    login(client, 'foo')
    response = client.post(USER_URI, data={'use_case': 'I want data.'})

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert b'has been rejected' in response.data


def test_post_user_approved(client, tables):
    tables.users_table.put_item(
        Item={
            'user_id': 'foo',
            'remaining_credits': Decimal(0),
            'application_status': APPLICATION_APPROVED,
        }
    )

    login(client, 'foo')
    response = client.post(USER_URI, data={'use_case': 'I want data.'})

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert b'is already approved' in response.data
