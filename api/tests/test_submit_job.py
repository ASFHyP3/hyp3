from datetime import datetime, timedelta, timezone

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


def test_submit_exceeds_quota(client, table, monkeypatch):
    login(client)
    time_for_previous_month = format_time(datetime.now(timezone.utc) - timedelta(days=32))
    job_from_previous_month = make_db_record('0ddaeb98-7636-494d-9496-03ea4a7df266',
                                             request_time=time_for_previous_month)
    table.put_item(Item=job_from_previous_month)

    monkeypatch.setenv('MONTHLY_JOB_QUOTA_PER_USER', '25')
    batch = [make_job() for ii in range(25)]
    setup_requests_mock(batch)

    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_200_OK

    response = submit_batch(client)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert '25 jobs' in response.json['detail']
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


def test_submit_job_without_name(client, table):
    login(client)
    batch = [
        make_job(name=None)
    ]
    setup_requests_mock(batch)

    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_200_OK


def test_submit_job_with_empty_name(client):
    login(client)
    batch = [
        make_job(name='')
    ]
    setup_requests_mock(batch)
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_submit_job_with_long_name(client):
    login(client)
    batch = [
        make_job(name='X' * 21)
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


def test_submit_good_granule_names(client, table):
    login(client)
    good_granule_names = [
        'S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38',
        'S1A_IW_SLC__1SSH_20150608T205059_20150608T205126_006287_0083E8_C4F0',
        'S1A_IW_GRDH_1SDV_20200604T190627_20200604T190652_032871_03CEB7_56F3',
        'S1A_IW_GRDH_1SSH_20171122T184459_20171122T184524_019381_020DD8_B825',
    ]
    for granule in good_granule_names:
        batch = [
            make_job(granule),
        ]
        setup_requests_mock(batch)
        response = submit_batch(client, batch)
        assert response.status_code == status.HTTP_200_OK


def test_submit_bad_granule_names(client):
    login(client)
    bad_granule_names = [
        'foo',
        'S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E3',
        'S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38_',
        # bad mission
        'S1C_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38',
        # bad beam modes
        'S1B_S3_SLC__1SDV_20200604T091417_20200604T091430_021882_029879_5765',
        'S1B_WV_SLC__1SSV_20200519T140110_20200519T140719_021651_0291AA_2A86',
        'S1B_EW_SLC__1SDH_20200605T065551_20200605T065654_021895_0298DC_EFB5',
        'S1A_EW_GRDH_1SDH_20171121T103939_20171121T104044_019362_020D26_CF9A',
        'S1B_S1_GRDH_1SDH_20171024T121032_20171024T121101_007971_00E153_F8F2',
        # bad product types
        'S1B_IW_OCN__2SDV_20200518T220815_20200518T220851_021642_02915F_B404',
        'S1B_IW_RAW__0SDV_20200605T145138_20200605T145210_021900_029903_AFF4',
        'S1A_IW_GRDM_1SDH_20190624T101121_20190624T101221_027820_0323FF_79E4',
    ]
    for granule in bad_granule_names:
        batch = [
            make_job(granule),
        ]
        setup_requests_mock(batch)
        response = submit_batch(client, batch)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_submit_validate_only(client, table):
    login(client)

    response = submit_batch(client, validate_only=True)
    assert response.status_code == status.HTTP_200_OK
    jobs = table.scan()['Items']
    assert len(jobs) == 0

    response = submit_batch(client, validate_only=False)
    assert response.status_code == status.HTTP_200_OK
    jobs = table.scan()['Items']
    assert len(jobs) == 1
