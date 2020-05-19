from os import environ

import pytest
from botocore.stub import Stubber
from flask_api import status
from hyp3_api import BATCH_CLIENT, connexion_app


@pytest.fixture
def client():
    with connexion_app.app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def batch_stub():
    with Stubber(BATCH_CLIENT) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


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


def test_submit_job(client, batch_stub):
    granule = 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9'
    add_response(batch_stub, granule, 'myJobId')
    response = client.post('/jobs', json={'granule': granule})
    assert response.status_code == status.HTTP_200_OK
    assert response.get_json() == {
        'jobId': 'myJobId',
        'jobName': 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9',
        'parameters': {
            'granule': 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9',
        },
    }


def test_granule_names(client, batch_stub):
    response = client.post('/jobs', json={'granule': 'foo'})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    granule = 'S1B_IW_OCN__2SDV_20200518T220815_20200518T220851_021642_02915F_B404'
    response = client.post('/jobs', json={'granule': granule})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    granule = 'S1B_S3_RAW__0SSV_20200518T185451_20200518T185522_021640_029151_BFBF'
    response = client.post('/jobs', json={'granule': granule})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    granule = 'S1A_S3_GRDH_1SDV_20200516T173131_20200516T173140_032593_03C66A_F005'
    response = client.post('/jobs', json={'granule': granule})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    granule = 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9'
    add_response(batch_stub, granule)
    response = client.post('/jobs', json={'granule': granule})
    assert response.status_code == status.HTTP_200_OK

    granule = 'S1A_EW_GRDM_1SDH_20200518T172837_20200518T172941_032622_03C745_422A'
    add_response(batch_stub, granule)
    response = client.post('/jobs', json={'granule': granule})
    assert response.status_code == status.HTTP_200_OK

    granule = 'S1A_IW_SLC__1SSH_20200518T142852_20200518T142919_032620_03C734_E5EE'
    add_response(batch_stub, granule)
    response = client.post('/jobs', json={'granule': granule})
    assert response.status_code == status.HTTP_200_OK


def test_jobs_bad_method(client):
    response = client.get('/jobs')
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    response = client.put('/jobs')
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    response = client.delete('/jobs')
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    response = client.head('/jobs')
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_no_route(client):
    response = client.get('/no/such/path')
    assert response.status_code == status.HTTP_404_NOT_FOUND
