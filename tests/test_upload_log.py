import pytest
from botocore.stub import Stubber

import upload_log


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


def test_get_log_stream():
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


def test_get_log_content(cloudwatch_stubber):
    expected_params = {'logGroupName': 'myLogGroup', 'logStreamName': 'myLogStream', 'startFromHead': True}
    service_response = {
        'events': [
            {'ingestionTime': 0, 'message': 'foo', 'timestamp': 0},
            {'ingestionTime': 1, 'message': 'bar', 'timestamp': 1},
        ],
        'nextForwardToken': 'myNextToken',
    }
    cloudwatch_stubber.add_response(method='get_log_events', expected_params=expected_params,
                                    service_response=service_response)

    expected_params = {'logGroupName': 'myLogGroup', 'logStreamName': 'myLogStream', 'startFromHead': True,
                       'nextToken': 'myNextToken'}
    service_response = {'events': [], 'nextForwardToken': 'myNextToken'}
    cloudwatch_stubber.add_response(method='get_log_events', expected_params=expected_params,
                                    service_response=service_response)

    assert upload_log.get_log_content('myLogGroup', 'myLogStream') == 'foo\nbar'


def test_upload_log_to_s3(s3_stubber):
    expected_params = {
        'Body': 'myContent',
        'Bucket': 'myBucket',
        'Key': 'myJobId/myJobId.log',
        'ContentType': 'text/plain',
    }
    tag_params = {
        'Bucket': 'myBucket',
        'Key': 'myJobId/myJobId.log',
        'Tagging': {
            'TagSet': [
                {'Key': 'file_type', 'Value': 'log'}
            ]
        }
    }
    s3_stubber.add_response(method='put_object', expected_params=expected_params, service_response={})
    s3_stubber.add_response(method='put_object_tagging', expected_params=tag_params, service_response={})

    upload_log.write_log_to_s3('myBucket', 'myJobId', 'myContent')
