from os import environ

import pytest
from botocore.stub import Stubber
from flask_api import status
from hyp3_api import BATCH_CLIENT, auth, connexion_app


AUTH_COOKIE = 'asf-urs'
JOBS_URI = '/jobs'


@pytest.fixture
def client():
    with connexion_app.app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def batch_stub():
    with Stubber(BATCH_CLIENT) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


def submit_job(client, granule, batch_stub=None):
    if batch_stub:
        add_response(batch_stub, granule)
    return client.post(JOBS_URI, json={'granule': granule})


def add_response(batch_stub, granule, job_id='myJobId'):
    batch_stub.add_response(
        method='submit_job',
        expected_params={
            'jobName': granule,
            'jobQueue': environ['JOB_QUEUE'],
            'jobDefinition': environ['JOB_DEFINITION'],
            'parameters': {
                'granule': granule,
            },
        },
        service_response={
            'jobId': job_id,
            'jobName': granule,
        },
    )


def login(client):
    client.set_cookie('localhost', AUTH_COOKIE, auth.get_mock_jwt_cookie('user'))


def test_submit_job(client, batch_stub):
    login(client)
    response = submit_job(client, 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9', batch_stub)
    assert response.status_code == status.HTTP_200_OK
    assert response.get_json() == {
        'jobId': 'myJobId',
        'parameters': {
            'granule': 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9',
        },
    }


def test_not_logged_in(client):
    response = submit_job(client, 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_invalid_cookie(client):
    client.set_cookie('localhost', AUTH_COOKIE, 'garbage I say!!! GARGBAGE!!!')
    response = submit_job(client, 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_expired_cookie(client):
    client.set_cookie('localhost', AUTH_COOKIE, auth.get_mock_jwt_cookie('user', -1))
    response = submit_job(client, 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_good_granule_names(client, batch_stub):
    login(client)
    response = submit_job(client, 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9', batch_stub)
    assert response.status_code == status.HTTP_200_OK

    response = submit_job(client, 'S1A_IW_GRDH_1SSH_20150609T141945_20150609T142014_006297_008439_B83E', batch_stub)
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
    response = client.get(JOBS_URI)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    response = client.put(JOBS_URI)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    response = client.delete(JOBS_URI)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    response = client.head(JOBS_URI)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_no_route(client):
    response = client.get('/no/such/path')
    assert response.status_code == status.HTTP_404_NOT_FOUND
