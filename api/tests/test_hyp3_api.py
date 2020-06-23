from os import environ
from time import time

import pytest
import yaml
from flask_api import status
from moto import mock_dynamodb2

from hyp3_api import DYNAMODB_RESOURCE, auth, connexion_app  # noqa hyp3 must be imported here

DEFAULT_USERNAME = 'test_username'

AUTH_COOKIE = 'asf-urs'
JOBS_URI = '/jobs'

DEFAULT_JOB_ID = 'myJobId'


@pytest.fixture
def client():
    with connexion_app.app.test_client() as test_client:
        yield test_client


@pytest.fixture
def table():
    table_properties = get_table_properties_from_template()
    with mock_dynamodb2():
        table = DYNAMODB_RESOURCE.create_table(
            TableName=environ['TABLE_NAME'],
            **table_properties,
        )
        yield table


def get_table_properties_from_template():
    yaml.SafeLoader.add_multi_constructor('!', lambda loader, suffix, node: None)
    with open('../cloudformation.yml', 'r') as f:
        template = yaml.safe_load(f)
    table_properties = template['Resources']['JobsTable']['Properties']
    return table_properties


def make_job(granule='S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38',
             description='someDescription',
             job_type='RTC_GAMMA'):
    job = {
        'job_type': job_type,
        'job_parameters': {
            'granule': granule
        }
    }
    if description is not None:
        job['description'] = description
    return job


def make_db_record(job_id,
                   granule='S1A_IW_SLC__1SDV_20200610T173646_20200610T173704_032958_03D14C_5F2B',
                   job_type='RTC_GAMMA',
                   user_id=DEFAULT_USERNAME,
                   request_time=1577836800,
                   status_code='RUNNING',
                   expiration_time=1577836800,
                   files=None):
    record = {
        'job_id': job_id,
        'user_id': user_id,
        'job_type': job_type,
        'job_parameters': {
            'granule': granule,
        },
        'request_time': request_time,
        'status_code': status_code,
    }
    if files is not None:
        record['files'] = files
    if expiration_time is not None:
        record['expiration_time'] = expiration_time
    return record


def submit_batch(client, batch=None):
    if batch is None:
        batch = [make_job()]
    return client.post(JOBS_URI, json={'jobs': batch})


def login(client, username=DEFAULT_USERNAME, authorized=True):
    client.set_cookie('localhost', AUTH_COOKIE, auth.get_mock_jwt_cookie(username, authorized=authorized))


def test_submit_one_job(client, table):
    login(client)
    response = submit_batch(client)
    assert response.status_code == status.HTTP_200_OK
    jobs = response.get_json()['jobs']
    assert len(jobs) == 1
    assert jobs[0]['status_code'] == 'PENDING'
    assert jobs[0]['request_time'] == int(time())
    assert jobs[0]['user_id'] == DEFAULT_USERNAME


def test_submit_many_jobs(client, table):
    max_jobs = 100
    login(client)

    batch = [make_job() for ii in range(max_jobs)]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_200_OK
    jobs = response.get_json()['jobs']
    assert len(jobs) == max_jobs
    assert len({job['request_time'] for job in jobs}) == 1

    batch.append(make_job())
    response = submit_batch(client, batch)
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


def test_list_jobs(client, table):
    files = [
        {
            'filename': 'foo.txt',
            'size': 123,
            'url': 'https://mybucket.s3.us-west-2.amazonaws.com/prefix/foo.txt',
        },
        {
            'filename': 'bar.png',
            'size': 0,
            'url': 'https://mybucket.s3.us-west-2.amazonaws.com/prefix/bar.png',
        },
    ]
    items = [
        make_db_record('0ddaeb98-7636-494d-9496-03ea4a7df266', user_id='user_with_jobs'),
        make_db_record('27836b79-e5b2-4d8f-932f-659724ea02c3', user_id='user_with_jobs', files=files)
    ]
    for item in items:
        table.put_item(Item=item)

    login(client, 'user_with_jobs')
    response = client.get(JOBS_URI)
    assert response.status_code == status.HTTP_200_OK
    assert response.json == {
        'jobs': items,
    }

    login(client, 'user_without_jobs')
    response = client.get(JOBS_URI)
    assert response.status_code == status.HTTP_200_OK
    assert response.json == {
        'jobs': [],
    }


def test_list_jobs_not_authorized(client, table):
    login(client, authorized=False)
    response = client.get(JOBS_URI)
    assert response.status_code == status.HTTP_200_OK
    assert response.json == {'jobs': []}


def test_list_jobs_by_status(client, table):
    items = [
        make_db_record('0ddaeb98-7636-494d-9496-03ea4a7df266', status_code='RUNNING'),
        make_db_record('27836b79-e5b2-4d8f-932f-659724ea02c3', status_code='SUCCEEDED')
    ]
    for item in items:
        table.put_item(Item=item)

    login(client)
    response = client.get(JOBS_URI, query_string={'status_code': 'RUNNING'})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json['jobs']) == 1
    assert response.json['jobs'][0] == items[0]

    response = client.get(JOBS_URI, query_string={'status_code': 'FAILED'})
    assert response.status_code == status.HTTP_200_OK
    assert response.json == {'jobs': []}


def test_list_jobs_bad_status(client):
    login(client)

    response = client.get(JOBS_URI, query_string={'status_code': 'BAD'})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.get(JOBS_URI, query_string={'status_code': ''})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_not_logged_in(client):
    response = submit_batch(client)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.get(JOBS_URI)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.head(JOBS_URI)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_logged_in_not_authorized(client):
    login(client, authorized=False)
    response = submit_batch(client)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_invalid_cookie(client):
    client.set_cookie('localhost', AUTH_COOKIE, 'garbage I say!!! GARGBAGE!!!')
    response = submit_batch(client)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_expired_cookie(client):
    client.set_cookie('localhost', AUTH_COOKIE, auth.get_mock_jwt_cookie('user', -1))
    response = submit_batch(client)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_good_granule_names(client, table):
    login(client)
    batch = [
        make_job('S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_200_OK

    batch = [
        make_job('S1A_IW_SLC__1SSH_20150608T205059_20150608T205126_006287_0083E8_C4F0')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_200_OK


def test_bad_granule_names(client):
    login(client)

    batch = [
        make_job('foo')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    batch = [
        make_job('S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E3')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    batch = [
        make_job('S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38_')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_bad_beam_modes(client):
    login(client)

    batch = [
        make_job('S1B_S3_SLC__1SDV_20200604T091417_20200604T091430_021882_029879_5765')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    batch = [
        make_job('S1B_WV_SLC__1SSV_20200519T140110_20200519T140719_021651_0291AA_2A86')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    batch = [
        make_job('S1B_EW_SLC__1SDH_20200605T065551_20200605T065654_021895_0298DC_EFB5')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_bad_product_types(client):
    login(client)

    batch = [
        make_job('S1A_IW_GRDH_1SDV_20200604T190627_20200604T190652_032871_03CEB7_56F3')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    batch = [
        make_job('S1B_IW_OCN__2SDV_20200518T220815_20200518T220851_021642_02915F_B404')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    batch = [
        make_job('S1B_IW_RAW__0SDV_20200605T145138_20200605T145210_021900_029903_AFF4')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_jobs_bad_method(client):
    response = client.put(JOBS_URI)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    response = client.delete(JOBS_URI)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_no_route(client):
    response = client.get('/no/such/path')
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_cors_no_origin(client):
    response = client.post(JOBS_URI)
    assert 'Access-Control-Allow-Origin' not in response.headers
    assert 'Access-Control-Allow-Credentials' not in response.headers


def test_cors_bad_origins(client):
    response = client.post(JOBS_URI, headers={'Origin': 'https://www.google.com'})
    assert 'Access-Control-Allow-Origin' not in response.headers
    assert 'Access-Control-Allow-Credentials' not in response.headers

    response = client.post(JOBS_URI, headers={'Origin': 'https://www.alaska.edu'})
    assert 'Access-Control-Allow-Origin' not in response.headers
    assert 'Access-Control-Allow-Credentials' not in response.headers


def test_cors_good_origins(client):
    response = client.post(JOBS_URI, headers={'Origin': 'https://search.asf.alaska.edu'})
    assert response.headers['Access-Control-Allow-Origin'] == 'https://search.asf.alaska.edu'
    assert response.headers['Access-Control-Allow-Credentials'] == 'true'

    response = client.post(JOBS_URI, headers={'Origin': 'https://search-test.asf.alaska.edu'})
    assert response.headers['Access-Control-Allow-Origin'] == 'https://search-test.asf.alaska.edu'
    assert response.headers['Access-Control-Allow-Credentials'] == 'true'

    response = client.post(JOBS_URI, headers={'Origin': 'http://local.asf.alaska.edu'})
    assert response.headers['Access-Control-Allow-Origin'] == 'http://local.asf.alaska.edu'
    assert response.headers['Access-Control-Allow-Credentials'] == 'true'
