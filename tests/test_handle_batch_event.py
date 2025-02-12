from unittest.mock import MagicMock, patch

import pytest

import handle_batch_event


@patch('dynamo.jobs.update_job')
@patch('dynamo.jobs.get_job')
def test_lambda_handler(mock_get_job: MagicMock, mock_update_job: MagicMock):
    event = {
        'source': 'aws.batch',
        'detail-type': 'Batch Job State Change',
        'detail': {'status': 'RUNNING', 'jobName': 'fooJob'},
    }
    mock_get_job.return_value = {'job_id': 'fooJob', 'status_code': 'PENDING'}

    handle_batch_event.lambda_handler(event, None)

    mock_get_job.assert_called_once_with('fooJob')
    mock_update_job.assert_called_once_with({'job_id': 'fooJob', 'status_code': 'RUNNING'})


@patch('dynamo.jobs.update_job')
@patch('dynamo.jobs.get_job')
def test_lambda_handler_job_not_pending(mock_get_job: MagicMock, mock_update_job: MagicMock):
    event = {
        'source': 'aws.batch',
        'detail-type': 'Batch Job State Change',
        'detail': {'status': 'RUNNING', 'jobName': 'fooJob'},
    }
    mock_get_job.return_value = {'job_id': 'fooJob', 'status_code': 'SUCCEEDED'}

    handle_batch_event.lambda_handler(event, None)

    mock_get_job.assert_called_once_with('fooJob')
    mock_update_job.assert_not_called()


def test_lambda_handler_invalid_source():
    event = {
        'source': 'dummy',
        'detail-type': 'Batch Job State Change',
        'detail': {'status': 'RUNNING', 'jobName': 'fooJob'},
    }
    with pytest.raises(ValueError, match=r'.* source .*'):
        handle_batch_event.lambda_handler(event, None)


def test_lambda_handler_invalid_detail_type():
    event = {'source': 'aws.batch', 'detail-type': 'dummy', 'detail': {'status': 'RUNNING', 'jobName': 'fooJob'}}
    with pytest.raises(ValueError, match=r'.* detail-type .*'):
        handle_batch_event.lambda_handler(event, None)


def test_lambda_handler_invalid_status():
    event = {
        'source': 'aws.batch',
        'detail-type': 'Batch Job State Change',
        'detail': {'status': 'dummy', 'jobName': 'fooJob'},
    }
    with pytest.raises(ValueError, match=r'.* status .*'):
        handle_batch_event.lambda_handler(event, None)


def test_lambda_handler_missing_key():
    event = {'detail-type': 'Batch Job State Change', 'detail': {'status': 'RUNNING', 'jobName': 'fooJob'}}
    with pytest.raises(KeyError, match=r"'source'"):
        handle_batch_event.lambda_handler(event, None)
