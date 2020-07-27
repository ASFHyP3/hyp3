from datetime import datetime, timedelta, timezone
from os import environ

from conftest import DEFAULT_USERNAME, login, make_db_record, make_job, setup_requests_mock, submit_batch
from flask_api import status

from hyp3_api.util import format_time


def test_submit_one_job(client, table):
    login(client)
    response = submit_batch(client)
    assert response.status_code == status.HTTP_200_OK
    jobs = response.json['jobs']
    assert len(jobs) == 1
    assert jobs[0]['status_code'] == 'PENDING'
    assert jobs[0]['request_time'] <= format_time(datetime.now(timezone.utc))
    assert jobs[0]['user_id'] == DEFAULT_USERNAME


def test_submit_many_jobs(client, table):
    max_jobs = 25
    login(client)

    batch = [make_job() for ii in range(max_jobs)]
    setup_requests_mock(batch)

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
    time_for_previous_month = format_time(datetime.now(timezone.utc) - timedelta(days=32))
    job_from_previous_month = make_db_record('0ddaeb98-7636-494d-9496-03ea4a7df266',
                                             request_time=time_for_previous_month)
    table.put_item(Item=job_from_previous_month)

    quota = int(environ['MONTHLY_JOB_QUOTA_PER_USER'])
    batch = [make_job() for ii in range(quota)]
    setup_requests_mock(batch)

    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_200_OK

    response = submit_batch(client)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert f'{quota} jobs' in response.json['detail']
    assert '0 jobs' in response.json['detail']


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
    setup_requests_mock(batch)

    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_200_OK


def test_submit_job_with_empty_description(client):
    login(client)
    batch = [
        make_job(description='')
    ]
    setup_requests_mock(batch)
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_submit_job_granule_does_not_exist(client, table):
    batch = [
        make_job('S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38'),
        make_job('S1A_IW_SLC__1SDV_20200610T173646_20200610T173704_032958_03D14C_5F2B')
    ]
    setup_requests_mock(batch)
    batch.append(make_job('S1A_IW_SLC__1SDV_20200610T173646_20200610T173704_032958_03D14C_5F2A'))

    login(client)
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json['title'] == 'Bad Request'
    assert response.json['detail'] == 'Some requested scenes could not be found: ' \
                                      'S1A_IW_SLC__1SDV_20200610T173646_20200610T173704_032958_03D14C_5F2A'
