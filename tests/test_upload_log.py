import os
from unittest.mock import MagicMock, patch

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
    result: dict = {
        'Container': {
            'LogStreamName': 'mySucceededLogStream',
        },
    }
    assert upload_log.get_log_stream(result) == 'mySucceededLogStream'

    result = {
        'Error': 'States.TaskFailed',
        'Cause': '{"Container": {"LogStreamName": "myFailedLogStream"}}',
    }
    assert upload_log.get_log_stream(result) == 'myFailedLogStream'

    result = {
        'Error': 'States.TaskFailed',
        'Cause': '{"Container": {}}',
    }
    assert upload_log.get_log_stream(result) is None


def test_get_log_content(cloudwatch_stubber):
    expected_params = {'logGroupName': 'myLogGroup', 'logStreamName': 'myLogStream', 'startFromHead': True}
    service_response = {
        'events': [
            {'ingestionTime': 0, 'message': 'foo', 'timestamp': 0},
            {'ingestionTime': 1, 'message': 'bar', 'timestamp': 1},
        ],
        'nextForwardToken': 'myNextToken',
    }
    cloudwatch_stubber.add_response(
        method='get_log_events', expected_params=expected_params, service_response=service_response
    )

    expected_params = {
        'logGroupName': 'myLogGroup',
        'logStreamName': 'myLogStream',
        'startFromHead': True,
        'nextToken': 'myNextToken',
    }
    service_response = {'events': [], 'nextForwardToken': 'myNextToken'}
    cloudwatch_stubber.add_response(
        method='get_log_events', expected_params=expected_params, service_response=service_response
    )

    assert upload_log.get_log_content('myLogGroup', 'myLogStream') == 'foo\nbar'


def test_get_log_content_from_failed_attempts():
    cause = {
        'Status': 'FAILED',
        'StatusReason': 'Task failed to start',
        'Attempts': [
            {'Container': {'Reason': 'error message 1'}},
            {'Container': {'Reason': 'error message 2'}},
            {'Container': {'Reason': 'error message 3'}},
        ],
    }
    expected = 'error message 1\nerror message 2\nerror message 3'
    assert upload_log.get_log_content_from_failed_attempts(cause) == expected


def test_get_log_content_from_failed_attempts_no_attempts():
    cause = {'Status': 'FAILED', 'StatusReason': 'foo reason', 'Attempts': []}
    expected = 'foo reason'
    assert upload_log.get_log_content_from_failed_attempts(cause) == expected


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
        'Tagging': {'TagSet': [{'Key': 'file_type', 'Value': 'log'}]},
    }
    s3_stubber.add_response(method='put_object', expected_params=expected_params, service_response={})
    s3_stubber.add_response(method='put_object_tagging', expected_params=tag_params, service_response={})

    upload_log.write_log_to_s3('myBucket', 'myJobId', 'myContent')


@patch('upload_log.write_log_to_s3')
@patch('upload_log.get_log_content')
@patch.dict(os.environ, {'BUCKET': 'test-bucket'}, clear=True)
def test_lambda_handler(mock_get_log_content: MagicMock, mock_write_log_to_s3: MagicMock):
    mock_get_log_content.return_value = 'here is some test log content'
    event = {
        'prefix': 'test-prefix',
        'log_group': 'test-log-group',
        'processing_results': {'step_0': {'Container': {'LogStreamName': 'test-log-stream'}}},
    }

    upload_log.lambda_handler(event, None)

    mock_get_log_content.assert_called_once_with('test-log-group', 'test-log-stream')
    mock_write_log_to_s3.assert_called_once_with('test-bucket', 'test-prefix', mock_get_log_content.return_value)


@patch('upload_log.write_log_to_s3')
@patch.dict(os.environ, {'BUCKET': 'test-bucket'}, clear=True)
def test_lambda_handler_no_log_stream(mock_write_log_to_s3: MagicMock):
    event = {
        'prefix': 'test-prefix',
        'log_group': 'test-log-group',
        'processing_results': {
            'step_0': {
                'Error': '',
                'Cause': '{"Container": {},' '"Status": "FAILED",' '"StatusReason": "foo reason",' '"Attempts": []}',
            }
        },
    }

    upload_log.lambda_handler(event, None)

    mock_write_log_to_s3.assert_called_once_with('test-bucket', 'test-prefix', 'foo reason')


def test_lambda_handler_log_stream_does_not_exist():
    def mock_get_log_events(**kwargs):
        assert kwargs['logGroupName'] == 'test-log-group'
        assert kwargs['logStreamName'] == 'test-log-stream'
        raise upload_log.CLOUDWATCH.exceptions.ResourceNotFoundException(
            {'Error': {'Message': 'The specified log stream does not exist.'}}, 'operation_name'
        )

    event = {
        'prefix': 'test-prefix',
        'log_group': 'test-log-group',
        'processing_results': {
            'step_0': {
                'Error': '',
                'Cause': '{"Container": {"LogStreamName": "test-log-stream"},'
                '"Status": "FAILED",'
                '"StatusReason": "Task failed to start",'
                '"Attempts": ['
                '{"Container": {"Reason": "error message 1"}},'
                '{"Container": {"Reason": "error message 2"}},'
                '{"Container": {"Reason": "error message 3"}}]}',
            }
        },
    }

    with (
        patch('upload_log.CLOUDWATCH.get_log_events', mock_get_log_events),
        patch('upload_log.write_log_to_s3') as mock_write_log_to_s3,
        patch.dict(os.environ, {'BUCKET': 'test-bucket'}, clear=True),
    ):
        upload_log.lambda_handler(event, None)

        mock_write_log_to_s3.assert_called_once_with(
            'test-bucket', 'test-prefix', 'error message 1\nerror message 2\nerror message 3'
        )


def test_lambda_handler_resource_not_found():
    def mock_get_log_events(**kwargs):
        assert kwargs['logGroupName'] == 'test-log-group'
        assert kwargs['logStreamName'] == 'test-log-stream'
        raise upload_log.CLOUDWATCH.exceptions.ResourceNotFoundException(
            {'Error': {'Message': 'foo message'}}, 'operation_name'
        )

    event = {
        'prefix': 'test-prefix',
        'log_group': 'test-log-group',
        'processing_results': {
            'step_0': {
                'Error': '',
                'Cause': '{"Container": {"LogStreamName": "test-log-stream"},'
                '"Status": "FAILED",'
                '"StatusReason": "Task failed to start",'
                '"Attempts": ['
                '{"Container": {"Reason": "error message 1"}},'
                '{"Container": {"Reason": "error message 2"}},'
                '{"Container": {"Reason": "error message 3"}}]}',
            }
        },
    }

    with patch('upload_log.CLOUDWATCH.get_log_events', mock_get_log_events):
        with pytest.raises(upload_log.CLOUDWATCH.exceptions.ResourceNotFoundException, match=r'.*foo message.*'):
            upload_log.lambda_handler(event, None)
