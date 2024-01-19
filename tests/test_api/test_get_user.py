from datetime import datetime, timezone
from http import HTTPStatus

from test_api.conftest import USER_URI, login, make_db_record

from dynamo.util import format_time


def test_get_new_user(client, tables, monkeypatch):
    monkeypatch.setenv('DEFAULT_CREDITS_PER_USER', '25')

    login(client, 'user')
    response = client.get(USER_URI)
    assert response.status_code == HTTPStatus.OK
    assert response.json == {
        'user_id': 'user',
        'remaining_credits': 25,
        'job_names': [],
    }


def test_get_existing_user(client, tables):
    user = {'user_id': 'user', 'remaining_credits': None}
    tables.users_table.put_item(Item=user)

    login(client, 'user')
    response = client.get(USER_URI)
    assert response.status_code == HTTPStatus.OK
    assert response.json == {
        'user_id': 'user',
        'remaining_credits': None,
        'job_names': [],
    }


def test_get_user_with_jobs(client, tables):
    user_id = 'user_with_jobs'
    user = {'user_id': user_id, 'remaining_credits': 20, 'foo': 'bar'}
    tables.users_table.put_item(Item=user)

    request_time = format_time(datetime.now(timezone.utc))
    items = [
        make_db_record('job1', user_id=user_id, request_time=request_time, status_code='PENDING', name='job1'),
        make_db_record('job2', user_id=user_id, request_time=request_time, status_code='RUNNING', name='job1'),
        make_db_record('job3', user_id=user_id, request_time=request_time, status_code='FAILED', name='job2'),
        make_db_record('job4', user_id=user_id, request_time=request_time, status_code='SUCCEEDED', name=None)
    ]
    for item in items:
        tables.jobs_table.put_item(Item=item)

    login(client, 'user_with_jobs')
    response = client.get(USER_URI)
    assert response.status_code == HTTPStatus.OK
    assert response.json == {
        'user_id': 'user_with_jobs',
        'remaining_credits': 20,
        'job_names': [
            'job1',
            'job2',
        ],
    }
