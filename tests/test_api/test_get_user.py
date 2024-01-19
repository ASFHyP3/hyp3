from datetime import datetime, timezone
from http import HTTPStatus

from test_api.conftest import USER_URI, login, make_db_record

from dynamo.util import format_time


# TODO update
def test_get_user(client, tables, monkeypatch):
    monkeypatch.setenv('MONTHLY_JOB_QUOTA_PER_USER', '25')
    request_time = format_time(datetime.now(timezone.utc))
    user = 'user_with_jobs'
    items = [
        make_db_record('job1', user_id=user, request_time=request_time, status_code='PENDING', name='job1'),
        make_db_record('job2', user_id=user, request_time=request_time, status_code='RUNNING', name='job1'),
        make_db_record('job3', user_id=user, request_time=request_time, status_code='FAILED', name='job2'),
        make_db_record('job4', user_id=user, request_time=request_time, status_code='SUCCEEDED', name=None)
    ]
    for item in items:
        tables.jobs_table.put_item(Item=item)

    login(client, 'user_with_jobs')
    response = client.get(USER_URI)
    assert response.status_code == HTTPStatus.OK
    assert response.json == {
        'user_id': 'user_with_jobs',
        'quota': {
            'max_jobs_per_month': 25,
            'remaining': 21,
        },
        'job_names': [
            'job1',
            'job2',
        ],
    }


# TODO update
def test_user_at_quota(client, tables, monkeypatch):
    monkeypatch.setenv('MONTHLY_JOB_QUOTA_PER_USER', '25')
    request_time = format_time(datetime.now(timezone.utc))

    items = [make_db_record(f'job{ii}', request_time=request_time) for ii in range(0, 24)]
    for item in items:
        tables.jobs_table.put_item(Item=item)

    login(client)
    response = client.get(USER_URI)
    assert response.status_code == HTTPStatus.OK
    assert response.json['quota']['remaining'] == 1

    tables.jobs_table.put_item(Item=make_db_record('anotherJob', request_time=request_time))
    response = client.get(USER_URI)
    assert response.status_code == HTTPStatus.OK
    assert response.json['quota']['remaining'] == 0

    tables.jobs_table.put_item(Item=make_db_record('yetAnotherJob', request_time=request_time))
    response = client.get(USER_URI)
    assert response.status_code == HTTPStatus.OK
    assert response.json['quota']['remaining'] == 0


def test_get_user_custom_quota(client, tables):
    username = 'user_with_custom_quota'
    login(client, username)
    tables.users_table.put_item(Item={'user_id': username, 'max_jobs_per_month': 50})

    response = client.get(USER_URI)
    assert response.status_code == HTTPStatus.OK
    assert response.json == {
        'user_id': username,
        'quota': {
            'max_jobs_per_month': 50,
            'remaining': 50,
        },
        'job_names': [],
    }


def test_get_user_no_quota(client, tables):
    username = 'user_with_no_quota'
    login(client, username)
    tables.users_table.put_item(Item={'user_id': username, 'max_jobs_per_month': None})

    response = client.get(USER_URI)
    assert response.status_code == HTTPStatus.OK
    assert response.json == {
        'user_id': username,
        'quota': {
            'max_jobs_per_month': None,
            'remaining': None,
        },
        'job_names': [],
    }
