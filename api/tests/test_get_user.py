from datetime import datetime, timezone
from os import environ

from conftest import USER_URI, login, make_db_record
from flask_api import status
from hyp3_api.util import format_time


QUOTA = int(environ['MONTHLY_JOB_QUOTA_PER_USER'])

# TODO:
# resets on
# user with no jobs

def test_get_user(client, table):
    request_time = format_time(datetime.now(timezone.utc))
    user = 'user_with_jobs'
    items = [
        make_db_record('job1', user_id=user, request_time=request_time, status_code='PENDING'),
        make_db_record('job2', user_id=user, request_time=request_time, status_code='RUNNING'),
        make_db_record('job3', user_id=user, request_time=request_time, status_code='FAILED'),
        make_db_record('job4', user_id=user, request_time=request_time, status_code='SUCCEEDED')
    ]
    for item in items:
        table.put_item(Item=item)

    login(client, 'user_with_jobs')
    response = client.get(USER_URI)
    assert response.status_code == status.HTTP_200_OK
    assert response.json == {
        'user_id': 'user_with_jobs',
        'authorized': True,
        'quota': {
            'limit': QUOTA,
            'remaining': QUOTA - 4,
        },
    }


def test_unauthoried_user(client, table):
    login(client, 'unauthorized_user', authorized=False)
    response = client.get(USER_URI)
    assert response.status_code == status.HTTP_200_OK
    assert response.json == {
        'user_id': 'unauthorized_user',
        'authorized': False,
        'quota': {
            'limit': 0,
            'remaining': 0,
        },
    }


def test_user_at_quota(client, table):
    request_time = format_time(datetime.now(timezone.utc))
    num_jobs = QUOTA - 1

    items = [make_db_record(f'job{ii}', request_time=request_time) for ii in range(0, num_jobs)]
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
