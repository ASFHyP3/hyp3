import pytest
from botocore.stub import Stubber

import upload_log


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv('BUCKET', 'myBucket')
    monkeypatch.setenv('AWS_REGION', 'myRegion')


@pytest.fixture
def cloudwatch_stubber():
    with Stubber(upload_log.CLOUDWATCH) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


@pytest.fixture
def s3_stubber():
    with Stubber(upload_log.S3) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


def test_get_log_stream(cloudwatch_stubber):
    processing_results = {
        'Container': {
            'LogStreamName': 'mySucceededLogStream',
        },
    }
    assert upload_log.get_log_stream(processing_results) == 'mySucceededLogStream'

    processing_results = {
        'Error': 'States.TaskFailed',
        'Cause': '{"Container": {"LogStreamName": "myFailedLogStream"}}',
    }
    assert upload_log.get_log_stream(processing_results) == 'myFailedLogStream'


def test_get_log_content():
    assert False


def test_upload_log_to_s3(s3_stubber):
    expected_params = {
        'Body': 'myContent',
        'Bucket': 'myBucket',
        'Key': 'myJobId/log.txt',
        'ContentType': 'text/plain',
    }
    tag_params = {
        'Bucket': 'myBucket',
        'Key': 'myJobId/log.txt',
        'Tagging': {
            'TagSet': [
                {'Key': 'file_type', 'Value': 'product'}
            ]
        }
    }
    s3_stubber.add_response(method='put_object', expected_params=expected_params, service_response={})
    s3_stubber.add_response(method='put_object_tagging', expected_params=tag_params, service_response={})

    upload_log.write_log_to_s3('myBucket', 'myJobId', 'myContent')
