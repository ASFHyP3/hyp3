from datetime import datetime, timezone

from conftest import USER_URI, login, make_db_record
from flask_api import status

from hyp3_api.util import format_time


def test_get_user(client, table, monkeypatch):
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
        table.put_item(Item=item)

    login(client, 'user_with_jobs')
    response = client.get(USER_URI)
    assert response.status_code == status.HTTP_200_OK
    assert response.json == {
        'user_id': 'user_with_jobs',
        'quota': {
            'limit': 25,
            'remaining': 21,
        },
        'names': [
            'job1',
            'job2',
        ],
    }


def test_user_at_quota(client, table, monkeypatch):
    monkeypatch.setenv('MONTHLY_JOB_QUOTA_PER_USER', '25')
    request_time = format_time(datetime.now(timezone.utc))

    items = [make_db_record(f'job{ii}', request_time=request_time) for ii in range(0, 24)]
    for item in items:
        table.put_item(Item=item)

    login(client)
    response = client.get(USER_URI)
    assert response.status_code == status.HTTP_200_OK
    assert response.json['quota']['remaining'] == 1

    table.put_item(Item=make_db_record('anotherJob', request_time=request_time))
    response = client.get(USER_URI)
    assert response.status_code == status.HTTP_200_OK
    assert response.json['quota']['remaining'] == 0

    table.put_item(Item=make_db_record('yetAnotherJob', request_time=request_time))
    response = client.get(USER_URI)
    assert response.status_code == status.HTTP_200_OK
    assert response.json['quota']['remaining'] == 0
