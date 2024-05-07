import json
import os
from decimal import Decimal
from unittest.mock import call, patch

import start_execution_manager


def test_invoke_worker():
    jobs = [
        {
            'job_id': 'job0',
            'decimal_float_field': Decimal('10.1'),
            'integer_float_field': Decimal('10'),
            'job_parameters': {
                'decimal_float_field': Decimal('10.1'),
                'integer_float_field': Decimal('10'),
                'decimal_list_field': [Decimal('10.1'), Decimal('10')]
            }
        },
        {
            'job_id': 'job1'
        }
    ]
    expected_payload = json.dumps(
        {
            'jobs': [
                {
                    'job_id': 'job0',
                    'decimal_float_field': 10.1,
                    'integer_float_field': 10,
                    'job_parameters': {
                        'decimal_float_field': 10.1,
                        'integer_float_field': 10,
                        'decimal_list_field': [10.1, 10]
                    }
                },
                {
                    'job_id': 'job1'
                }
            ]
        }
    )
    with patch('start_execution_manager.LAMBDA_CLIENT.invoke') as mock_invoke:
        mock_invoke.return_value = 'test-response'

        assert start_execution_manager.invoke_worker('test-worker-arn', jobs) == 'test-response'

        mock_invoke.assert_called_once_with(
            FunctionName='test-worker-arn',
            InvocationType='Event',
            Payload=expected_payload,
        )


def test_lambda_handler_500_jobs():
    with patch('dynamo.jobs.get_jobs_waiting_for_execution') as mock_get_jobs_waiting_for_execution, \
            patch('start_execution_manager.invoke_worker') as mock_invoke_worker, \
            patch.dict(os.environ, {'START_EXECUTION_WORKER_ARN': 'test-worker-function-arn'}, clear=True):
        mock_jobs = list(range(500))
        mock_get_jobs_waiting_for_execution.return_value = mock_jobs

        mock_invoke_worker.return_value = {'StatusCode': None}

        start_execution_manager.lambda_handler(None, None)

        mock_get_jobs_waiting_for_execution.assert_called_once_with(limit=500)

        assert mock_invoke_worker.mock_calls == [
            call('test-worker-function-arn', mock_jobs[0:250]),
            call('test-worker-function-arn', mock_jobs[250:500]),
        ]


def test_lambda_handler_400_jobs():
    with patch('dynamo.jobs.get_jobs_waiting_for_execution') as mock_get_jobs_waiting_for_execution, \
            patch('start_execution_manager.invoke_worker') as mock_invoke_worker, \
            patch.dict(os.environ, {'START_EXECUTION_WORKER_ARN': 'test-worker-function-arn'}, clear=True):
        mock_jobs = list(range(400))
        mock_get_jobs_waiting_for_execution.return_value = mock_jobs

        mock_invoke_worker.return_value = {'StatusCode': None}

        start_execution_manager.lambda_handler(None, None)

        mock_get_jobs_waiting_for_execution.assert_called_once_with(limit=500)

        assert mock_invoke_worker.mock_calls == [
            call('test-worker-function-arn', mock_jobs[0:250]),
            call('test-worker-function-arn', mock_jobs[250:400]),
        ]


def test_lambda_handler_50_jobs():
    with patch('dynamo.jobs.get_jobs_waiting_for_execution') as mock_get_jobs_waiting_for_execution, \
            patch('start_execution_manager.invoke_worker') as mock_invoke_worker, \
            patch.dict(os.environ, {'START_EXECUTION_WORKER_ARN': 'test-worker-function-arn'}, clear=True):
        mock_jobs = list(range(50))
        mock_get_jobs_waiting_for_execution.return_value = mock_jobs

        mock_invoke_worker.return_value = {'StatusCode': None}

        start_execution_manager.lambda_handler(None, None)

        mock_get_jobs_waiting_for_execution.assert_called_once_with(limit=500)

        assert mock_invoke_worker.mock_calls == [
            call('test-worker-function-arn', mock_jobs),
        ]


def test_lambda_handler_no_jobs():
    with patch('dynamo.jobs.get_jobs_waiting_for_execution') as mock_get_jobs_waiting_for_execution, \
            patch('start_execution_manager.invoke_worker') as mock_invoke_worker, \
            patch.dict(os.environ, {'START_EXECUTION_WORKER_ARN': 'test-worker-function-arn'}, clear=True):
        mock_get_jobs_waiting_for_execution.return_value = []

        start_execution_manager.lambda_handler(None, None)

        mock_get_jobs_waiting_for_execution.assert_called_once_with(limit=500)

        mock_invoke_worker.assert_not_called()
