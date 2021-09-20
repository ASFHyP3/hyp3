import json

import pytest
from botocore.stub import Stubber

import daemon
import upload_log


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv('ACTIVITY_ARN', 'myActivity')


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


@pytest.fixture
def sfn_stubber():
    with Stubber(daemon.SFN_CLIENT) as stubber:
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


def test_get_task(sfn_stubber):
    expected_params = {
        'activityArn': 'myActivity'
    }
    expected_input = {'foo': 'bar', 'baz': 1}
    response = {'input': json.dumps(expected_input), 'taskToken': 'myTask'}
    sfn_stubber.add_response(method='get_activity_task', expected_params=expected_params,
                             service_response=response)

    task = daemon.get_task()
    assert json.loads(task['input']) == expected_input
    assert task['taskToken'] == 'myTask'

    sfn_stubber.add_response(method='get_activity_task', expected_params=expected_params,
                             service_response={})

    task = daemon.get_task()
    assert task == {}


def test_send_task_response(sfn_stubber):
    expected_params = {
        'output': '{}',
        'taskToken': 'myTask'
    }
    sfn_stubber.add_response('send_task_success', expected_params=expected_params, service_response={})
    daemon.send_task_response({'taskToken': 'myTask'})

    expected_params = {
        'error': 'MyError',
        'cause': 'myCause',
        'taskToken': 'myTask'
    }
    sfn_stubber.add_response('send_task_failure', expected_params=expected_params, service_response={})

    class MyError(Exception):
        pass

    daemon.send_task_response({'taskToken': 'myTask'}, error=MyError('myCause'))
