from datetime import datetime
from json import dumps
from os import environ

import pytest
from botocore.stub import Stubber
from flask_api import status
from moto import mock_dynamodb2

from hyp3_api import DYNAMODB_RESOURCE, STEP_FUNCTION_CLIENT, auth, connexion_app  # noqa hyp3 must be imported here

AUTH_COOKIE = 'asf-urs'
JOBS_URI = '/jobs'

DEFAULT_JOB_ID = 'myJobId'
DEFAULT_GRANULE = 'S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38'
DEFAULT_DESCRIPTION = 'someDescription'
DEFAULT_JOB_TYPE = 'RTC_GAMMA'


@pytest.fixture
def client():
    with connexion_app.app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def states_stub():
    with Stubber(STEP_FUNCTION_CLIENT) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


def make_job(granule=DEFAULT_GRANULE, description=DEFAULT_DESCRIPTION, job_type=DEFAULT_JOB_TYPE):
    job = {
        'job_type': job_type,
        'job_parameters': {
            'granule': granule
        }
    }
    if description is not None:
        job['description'] = description
    return job


def submit_batch(client, batch=None, states_stub=None):
    if not batch:
        batch = [make_job()]
    if states_stub:
        for job in batch:
            stub_response(states_stub, job)

    return client.post(JOBS_URI, json={'jobs': batch})


def stub_response(states_stub, job):
    payload = job.copy()
    payload['user_id'] = 'test_username'
    states_stub.add_response(
        method='start_execution',
        expected_params={
            'stateMachineArn': environ['STEP_FUNCTION_ARN'],
            'input': dumps(payload, sort_keys=True),
        },
        service_response={
            'executionArn': f'{environ["STEP_FUNCTION_ARN"]}:{DEFAULT_JOB_ID}',
            'startDate': datetime.utcnow(),
        },
    )


def login(client, username='test_username', authorized=True):
    client.set_cookie('localhost', AUTH_COOKIE, auth.get_mock_jwt_cookie(username, authorized=authorized))


def test_submit_job(client, states_stub):
    login(client)
    response = submit_batch(client, states_stub=states_stub)
    assert response.status_code == status.HTTP_200_OK
    assert response.get_json() == [
        {'job_id': DEFAULT_JOB_ID}
    ]


def test_submit_job_without_description(client):
    login(client)
    batch = [
        make_job(description=None)
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_submit_job_with_empty_description(client, states_stub):
    login(client)
    batch = [
        make_job(description='')
    ]
    response = submit_batch(client, batch=batch, states_stub=states_stub)
    assert response.status_code == status.HTTP_200_OK


@mock_dynamodb2
def test_list_jobs(client):
    table = DYNAMODB_RESOURCE.create_table(
        TableName=environ['TABLE_NAME'],
        AttributeDefinitions=[
            {
                'AttributeName': 'job_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'user_id',
                'AttributeType': 'S',
            },

        ],
        KeySchema=[
            {
                'AttributeName': 'job_id',
                'KeyType': 'HASH',
            },
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'user_id',
                'KeySchema': [
                    {
                        'AttributeName': 'user_id',
                        'KeyType': 'HASH',
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                },
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 15,
            'WriteCapacityUnits': 15,
        },
    )

    items = [
        {
            'job_id': '0ddaeb98-7636-494d-9496-03ea4a7df266',
            'user_id': 'user_with_jobs',
            'job_parameters': {
                'granule': 'S1A_IW_GRDH_1SDV_20200426T125708_20200426T125733_032299_03BCC4_A4E0',
            },
        },
        {
            'job_id': '27836b79-e5b2-4d8f-932f-659724ea02c3',
            'user_id': 'user_with_jobs',
            'job_parameters': {
                'granule': 'S1B_IW_GRDH_1SDV_20200604T044748_20200604T044813_021879_029863_93A4',
            },
        },
    ]
    for item in items:
        table.put_item(Item=item)

    login(client, 'user_with_jobs', authorized=False)
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


def test_good_granule_names(client, states_stub):
    login(client)
    batch = [
        make_job('S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38')
    ]
    response = submit_batch(client, batch, states_stub)
    assert response.status_code == status.HTTP_200_OK

    batch = [
        make_job('S1A_IW_SLC__1SSH_20150608T205059_20150608T205126_006287_0083E8_C4F0')
    ]
    response = submit_batch(client, batch, states_stub)
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
