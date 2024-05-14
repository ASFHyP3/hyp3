import unittest.mock
from decimal import Decimal
from http import HTTPStatus

from test_api.conftest import DEFAULT_ACCESS_TOKEN, USER_URI, login

from dynamo.user import APPLICATION_APPROVED, APPLICATION_NOT_STARTED, APPLICATION_PENDING, APPLICATION_REJECTED


def test_post_user(client, tables):
    login(client, 'foo')
    with unittest.mock.patch('dynamo.user.get_edl_profile') as mock_get_edl_profile:
        mock_get_edl_profile.return_value = {'email_address': 'foo@example.com'}
        response = client.post(USER_URI, data={'use_case': 'I want data.'})
        mock_get_edl_profile.assert_called_once_with('foo', DEFAULT_ACCESS_TOKEN)

    assert response.status_code == HTTPStatus.OK
    assert b'successfully requested access to HyP3 for <b>foo</b>' in response.data
    assert b'email you at <b>foo@example.com</b>' in response.data


def test_post_user_not_started(client, tables):
    tables.users_table.put_item(
        Item={
            'user_id': 'foo',
            'remaining_credits': Decimal(0),
            'application_status': APPLICATION_NOT_STARTED,
        }
    )

    login(client, 'foo')
    with unittest.mock.patch('dynamo.user.get_edl_profile') as mock_get_edl_profile:
        mock_get_edl_profile.return_value = {'email_address': 'foo@example.com'}
        response = client.post(USER_URI, data={'use_case': 'I want data.'})
        mock_get_edl_profile.assert_called_once_with('foo', DEFAULT_ACCESS_TOKEN)

    assert response.status_code == HTTPStatus.OK
    assert b'successfully requested access to HyP3 for <b>foo</b>' in response.data
    assert b'email you at <b>foo@example.com</b>' in response.data


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
    assert b"<b>foo</b>'s request for access is pending review" in response.data


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
    assert b"<b>foo</b>'s request for access has been rejected" in response.data


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
    assert b"<b>foo</b>'s request for access has already been approved" in response.data
