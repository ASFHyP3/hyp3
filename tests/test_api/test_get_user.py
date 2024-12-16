from http import HTTPStatus

from test_api.conftest import USER_URI, login, make_db_record

from dynamo.user import APPLICATION_APPROVED, APPLICATION_NOT_STARTED, APPLICATION_REJECTED
from dynamo.util import current_utc_time


def test_get_new_user(client, tables, monkeypatch):
    login(client, 'user')
    response = client.get(USER_URI)
    assert response.status_code == HTTPStatus.OK
    assert response.json == {
        'user_id': 'user',
        'application_status': APPLICATION_NOT_STARTED,
        'remaining_credits': 0,
        'job_names': [],
    }


def test_get_rejected_user(client, tables):
    user = {'user_id': 'user', 'remaining_credits': 100, 'application_status': APPLICATION_REJECTED}
    tables.users_table.put_item(Item=user)

    login(client, 'user')
    response = client.get(USER_URI)
    assert response.status_code == HTTPStatus.OK
    assert response.json == {
        'user_id': 'user',
        'application_status': APPLICATION_REJECTED,
        'remaining_credits': 0,
        'job_names': [],
    }


def test_get_user_with_jobs(client, tables):
    user_id = 'user_with_jobs'
    user = {
        'user_id': user_id,
        'remaining_credits': 20,
        'application_status': APPLICATION_APPROVED,
        'credits_per_month': 50,
        '_month_of_last_credit_reset': '2024-01-01',
        '_foo': 'bar',
    }
    tables.users_table.put_item(Item=user)

    request_time = current_utc_time()
    items = [
        make_db_record('job1', user_id=user_id, request_time=request_time, status_code='PENDING', name='job1'),
        make_db_record('job2', user_id=user_id, request_time=request_time, status_code='RUNNING', name='job1'),
        make_db_record('job3', user_id=user_id, request_time=request_time, status_code='FAILED', name='job2'),
        make_db_record('job4', user_id=user_id, request_time=request_time, status_code='SUCCEEDED', name=None),
    ]
    for item in items:
        tables.jobs_table.put_item(Item=item)

    login(client, 'user_with_jobs')
    response = client.get(USER_URI)
    assert response.status_code == HTTPStatus.OK
    assert response.json == {
        'user_id': 'user_with_jobs',
        'application_status': APPLICATION_APPROVED,
        'credits_per_month': 50,
        'remaining_credits': 50,
        'job_names': [
            'job1',
            'job2',
        ],
    }
