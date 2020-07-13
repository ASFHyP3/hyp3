from os import environ
from datetime import datetime, timezone

from flask_api import status

from conftest import make_db_record, login
from hyp3_api.util import format_time
USER_URI = '/user'

# TODO:
# unauthorized user
# resets on
# user with no jobs
# user with jobs > quota
def test_get_user(client, table):
    request_time = format_time(datetime.now(timezone.utc))
    items = [
        make_db_record('0ddaeb98-7636-494d-9496-03ea4a7df266', user_id='user_with_jobs', request_time=request_time),
        make_db_record('27836b79-e5b2-4d8f-932f-659724ea02c3', user_id='user_with_jobs', request_time=request_time)
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
            'limit': int(environ['MONTHLY_JOB_QUOTA_PER_USER']),
            'remaining': int(environ['MONTHLY_JOB_QUOTA_PER_USER']) - 2,
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
