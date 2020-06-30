from datetime import datetime, timedelta
from os import environ

from conftest import DEFAULT_USERNAME, login, make_db_record, make_job, submit_batch
from flask_api import status

from hyp3_api.handlers import format_time


def test_submit_one_job(client, table):
    login(client)
    response = submit_batch(client)
    assert response.status_code == status.HTTP_200_OK
    jobs = response.json['jobs']
    assert len(jobs) == 1
    assert jobs[0]['status_code'] == 'PENDING'
    assert jobs[0]['request_time'] <= format_time(datetime.utcnow())
    assert jobs[0]['user_id'] == DEFAULT_USERNAME


def test_submit_many_jobs(client, table):
    max_jobs = 100
    login(client)

    batch = [make_job() for ii in range(max_jobs)]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_200_OK
    jobs = response.json['jobs']
    distinct_request_times = {job['request_time'] for job in jobs}
    assert len(jobs) == max_jobs
    assert len(distinct_request_times) == 1

    batch.append(make_job())
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_submit_exceeds_quota(client, table):
    login(client)
    time_for_previous_month = (datetime.utcnow() - timedelta(days=32)).isoformat('T')
    job_from_previous_month = make_db_record('0ddaeb98-7636-494d-9496-03ea4a7df266',
                                             request_time=time_for_previous_month)
    table.put_item(Item=job_from_previous_month)

    batch = [make_job() for ii in range(int(environ['MONTHLY_JOB_QUOTA_PER_USER']))]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_200_OK

    response = submit_batch(client)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_submit_without_jobs(client):
    login(client)
    batch = []
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_submit_job_without_description(client, table):
    login(client)
    batch = [
        make_job(description=None)
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_200_OK


def test_submit_job_with_empty_description(client):
    login(client)
    batch = [
        make_job(description='')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
