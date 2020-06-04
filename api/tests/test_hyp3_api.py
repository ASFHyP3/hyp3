from datetime import datetime
from json import dumps
from os import environ

import pytest
import boto3
from botocore.stub import Stubber
import hyp3_api
from flask_api import status
from hyp3_api import STEP_FUNCTION_CLIENT, auth, connexion_app
from moto import mock_dynamodb2

AUTH_COOKIE = 'asf-urs'
JOBS_URI = '/jobs'


@pytest.fixture
def client():
    with connexion_app.app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def states_stub():
    with Stubber(STEP_FUNCTION_CLIENT) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


def submit_job(client, granule, states_stub=None):
    if states_stub:
        stub_response(states_stub, granule)
    payload = {
        'process_type': 'RTC_GAMMA',
        'parameters': {
            'granule': granule
        }
    }
    return client.post(JOBS_URI, json=payload)


def stub_response(states_stub, granule):
    payload = {
        'user_id': 'test_username',
        'parameters': {
            'granule': granule,
        },
        'process_type': 'RTC_GAMMA',
    }
    states_stub.add_response(
        method='start_execution',
        expected_params={
            'stateMachineArn': environ['STEP_FUNCTION_ARN'],
            'input': dumps(payload, sort_keys=True),
        },
        service_response={
            'executionArn': f'{environ["STEP_FUNCTION_ARN"]}:myJobId',
            'startDate': datetime.utcnow(),
        },
    )


def login(client, username='test_username'):
    client.set_cookie('localhost', AUTH_COOKIE, auth.get_mock_jwt_cookie(username))


def test_submit_job(client, states_stub):
    login(client)
    response = submit_job(client, 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9', states_stub)
    assert response.status_code == status.HTTP_200_OK
    assert response.get_json() == {
        'jobId': 'myJobId',
    }


@mock_dynamodb2
def test_list_jobs(client):
    table_name = environ['TABLE_NAME']
    hyp3_api.DYNAMODB_RESOURCE = boto3.resource('dynamodb')

    table = hyp3_api.DYNAMODB_RESOURCE.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'job_id',
                'KeyType': 'HASH'
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
                    'ProjectionType': 'ALL'
                }
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'job_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'user_id',
                'AttributeType': 'S'
            },

        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 15,
            'WriteCapacityUnits': 15
        }
    )

    items = [
        {
            'job_id': '0ddaeb98-7636-494d-9496-03ea4a7df266',
            'user_id': 'user_with_jobs',
            'parameters': {
                'granule': 'S1A_IW_GRDH_1SDV_20200426T125708_20200426T125733_032299_03BCC4_b4E0'
            },
        },
        {
            'job_id': '27836b79-e5b2-4d8f-932f-659724ea02c3',
            'user_id': 'user_with_jobs',
            'parameters': {
                'granule': 'S1B_IW_GRDH_1SDV_20200604T044748_20200604T044813_021879_029863_93A4'
            },
        },
    ]
    for item in items:
        table.put_item(Item=item)

    login(client, 'user_with_jobs')
    response = client.get(JOBS_URI)
    assert response.status_code == status.HTTP_200_OK
    assert response.json == {
        'jobs': [
            {
                'job_id': '0ddaeb98-7636-494d-9496-03ea4a7df266',
                'user_id': 'user_with_jobs',
                'parameters': {
                    'granule': 'S1A_IW_GRDH_1SDV_20200426T125708_20200426T125733_032299_03BCC4_b4E0',
                },
            },
            {
                'job_id': '27836b79-e5b2-4d8f-932f-659724ea02c3',
                'user_id': 'user_with_jobs',
                'parameters': {
                    'granule': 'S1B_IW_GRDH_1SDV_20200604T044748_20200604T044813_021879_029863_93A4',
                },
            },
        ]
    }

    login(client, 'user_without_jobs')
    response = client.get(JOBS_URI)
    assert response.status_code == status.HTTP_200_OK
    assert response.json == {'jobs': []}


def test_not_logged_in(client):
    response = submit_job(client, 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.get(JOBS_URI)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.head(JOBS_URI)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_invalid_cookie(client):
    client.set_cookie('localhost', AUTH_COOKIE, 'garbage I say!!! GARGBAGE!!!')
    response = submit_job(client, 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_expired_cookie(client):
    client.set_cookie('localhost', AUTH_COOKIE, auth.get_mock_jwt_cookie('user', -1))
    response = submit_job(client, 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_good_granule_names(client, states_stub):
    login(client)
    response = submit_job(client, 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9', states_stub)
    assert response.status_code == status.HTTP_200_OK

    response = submit_job(client, 'S1A_IW_GRDH_1SSH_20150609T141945_20150609T142014_006297_008439_B83E', states_stub)
    assert response.status_code == status.HTTP_200_OK


def test_bad_granule_names(client):
    login(client)
    response = submit_job(client, 'foo')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = submit_job(client, 'S1A_IW_GRDH_1SSH_20150609T141945_20150609T142014_006297_008439_B83')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = submit_job(client, 'S1A_IW_GRDH_1SSH_20150609T141945_20150609T142014_006297_008439_B83Ea')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = submit_job(client, 'S1A_S3_GRDH_1SDV_20200516T173131_20200516T173140_032593_03C66A_F005')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = submit_job(client, 'S1A_EW_GRDM_1SDH_20200518T172837_20200518T172941_032622_03C745_422A')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = submit_job(client, 'S1A_IW_SLC__1SSH_20200518T142852_20200518T142919_032620_03C734_E5EE')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = submit_job(client, 'S1B_IW_OCN__2SDV_20200518T220815_20200518T220851_021642_02915F_B404')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = submit_job(client, 'S1B_S3_RAW__0SSV_20200518T185451_20200518T185522_021640_029151_BFBF')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = submit_job(client, 'S1B_WV_SLC__1SSV_20200519T140110_20200519T140719_021651_0291AA_2A86')
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
