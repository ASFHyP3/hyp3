import unittest.mock
from decimal import Decimal
from http import HTTPStatus

from test_api.conftest import DEFAULT_ACCESS_TOKEN, USER_URI, login

from dynamo.user import APPLICATION_APPROVED, APPLICATION_PENDING, APPLICATION_REJECTED


def test_patch_new_user(client, tables):
    login(client, 'foo')
    with unittest.mock.patch('dynamo.user._get_edl_profile') as mock_get_edl_profile:
        mock_get_edl_profile.return_value = {}
        response = client.patch(USER_URI, json={'use_case': 'I want data.'})
        mock_get_edl_profile.assert_called_once_with('foo', DEFAULT_ACCESS_TOKEN)

    assert response.status_code == HTTPStatus.OK
    assert response.json == {
        'user_id': 'foo',
        'application_status': APPLICATION_PENDING,
        'remaining_credits': 0,
        'job_names': [],
        'use_case': 'I want data.',
    }


def test_patch_pending_user(client, tables):
    tables.users_table.put_item(
        Item={
            'user_id': 'foo',
            'remaining_credits': Decimal(5),
            'application_status': APPLICATION_PENDING,
            'use_case': 'Old use case.',
            '_edl_profile': {},
            '_foo': 'bar',
        }
    )

    login(client, 'foo')
    with unittest.mock.patch('dynamo.user._get_edl_profile') as mock_get_edl_profile:
        mock_get_edl_profile.return_value = {}
        response = client.patch(USER_URI, json={'use_case': 'New use case.'})
        mock_get_edl_profile.assert_called_once_with('foo', DEFAULT_ACCESS_TOKEN)

    assert response.status_code == HTTPStatus.OK
    assert response.json == {
        'user_id': 'foo',
        'remaining_credits': 0,
        'application_status': APPLICATION_PENDING,
        'use_case': 'New use case.',
        'job_names': [],
    }


def test_patch_rejected_user(client, tables):
    tables.users_table.put_item(
        Item={
            'user_id': 'foo',
            'remaining_credits': Decimal(0),
            'application_status': APPLICATION_REJECTED,
        }
    )

    login(client, 'foo')
    response = client.patch(USER_URI, json={'use_case': 'I want data.'})

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert 'has been rejected' in response.json['detail']


def test_patch_user_access_code(client, tables):
    tables.access_codes_table.put_item(
        Item={'access_code': '123', 'start_date': '2024-05-21T20:01:03+00:00', 'end_date': '2024-05-21T20:01:04+00:00'}
    )
    login(client, 'foo')

    with unittest.mock.patch('dynamo.util.current_utc_time') as mock_current_utc_time, \
            unittest.mock.patch('dynamo.user._get_edl_profile') as mock_get_edl_profile:

        mock_current_utc_time.return_value = '2024-05-21T20:01:03+00:00'
        mock_get_edl_profile.return_value = {}

        response = client.patch(
            USER_URI,
            json={'use_case': 'I want data.', 'access_code': '123'}
        )

        mock_current_utc_time.assert_called_once_with()
        mock_get_edl_profile.assert_called_once_with('foo', DEFAULT_ACCESS_TOKEN)

    assert response.status_code == HTTPStatus.OK
    assert response.json == {
        'user_id': 'foo',
        'application_status': APPLICATION_APPROVED,
        'remaining_credits': 25,
        'job_names': [],
        'use_case': 'I want data.',
        'access_code': '123',
    }


def test_patch_user_access_code_start_date(client, tables):
    tables.access_codes_table.put_item(
        Item={'access_code': '123', 'start_date': '2024-05-21T20:01:03+00:00'}
    )
    login(client, 'foo')

    with unittest.mock.patch('dynamo.util.current_utc_time') as mock_current_utc_time:
        mock_current_utc_time.return_value = '2024-05-21T20:01:02+00:00'
        response = client.patch(
            USER_URI,
            json={'use_case': 'I want data.', 'access_code': '123'}
        )
        mock_current_utc_time.assert_called_once_with()

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert 'will become active' in response.json['detail']


def test_patch_user_access_code_end_date(client, tables):
    tables.access_codes_table.put_item(
        Item={'access_code': '123', 'start_date': '2024-05-21T20:01:03+00:00', 'end_date': '2024-05-21T20:01:04+00:00'}
    )
    login(client, 'foo')

    with unittest.mock.patch('dynamo.util.current_utc_time') as mock_current_utc_time:
        mock_current_utc_time.return_value = '2024-05-21T20:01:04+00:00'
        response = client.patch(
            USER_URI,
            json={'use_case': 'I want data.', 'access_code': '123'}
        )
        mock_current_utc_time.assert_called_once_with()

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert 'expired' in response.json['detail']


def test_patch_user_access_code_invalid(client, tables):
    tables.access_codes_table.put_item(
        Item={'access_code': '123'}
    )
    login(client, 'foo')

    response = client.patch(
        USER_URI,
        json={'use_case': 'I want data.', 'access_code': '456'}
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert 'not a valid access code' in response.json['detail']
