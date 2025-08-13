import json
import os
from unittest.mock import call, patch

import start_execution


def test_convert_to_string():
    assert start_execution.convert_to_string(1) == '1'
    assert start_execution.convert_to_string(True) == 'True'
    assert start_execution.convert_to_string([1, 2]) == '1 2'
    assert start_execution.convert_to_string(['abc', 'bcd']) == 'abc bcd'
    assert start_execution.convert_to_string('abc') == 'abc'


def test_submit_jobs():
    batch_params_by_job_type = {
        'JOB_0': ['granules', 'string_field', 'boolean_field', 'float_field', 'integer_field'],
        'JOB_1': ['string_field', 'boolean_field'],
        'JOB_2': [],
    }

    jobs = [
        {
            'job_id': 'job0',
            'job_type': 'JOB_0',
            'string_field': 'value1',
            'boolean_field': True,
            'float_field': 10.1,
            'integer_field': 10,
            'job_parameters': {
                'granules': [
                    'granule1',
                    'granule2',
                ],
                'string_field': 'value1',
                'boolean_field': True,
                'float_field': 10.1,
                'integer_field': 10,
            },
        },
        {
            'job_id': 'job1',
            'job_type': 'JOB_1',
            'string_field': 'value1',
            'boolean_field': True,
            'float_field': 10.1,
            'integer_field': 10,
            'job_parameters': {
                'granules': [
                    'granule1',
                    'granule2',
                ],
                'string_field': 'value1',
                'boolean_field': True,
                'float_field': 10.1,
                'integer_field': 10,
            },
        },
        {
            'job_id': 'job2',
            'job_type': 'JOB_2',
            'string_field': 'value1',
            'boolean_field': True,
            'float_field': 10.1,
            'integer_field': 10,
            'job_parameters': {
                'granules': [
                    'granule1',
                    'granule2',
                ],
                'string_field': 'value1',
                'boolean_field': True,
                'float_field': 10.1,
                'integer_field': 10,
            },
        },
    ]

    expected_input_job0 = json.dumps(
        {
            'job_id': 'job0',
            'job_type': 'JOB_0',
            'string_field': 'value1',
            'boolean_field': True,
            'float_field': 10.1,
            'integer_field': 10,
            'job_parameters': {
                'granules': [
                    'granule1',
                    'granule2',
                ],
                'string_field': 'value1',
                'boolean_field': True,
                'float_field': 10.1,
                'integer_field': 10,
            },
            'batch_job_parameters': {
                'granules': 'granule1 granule2',
                'string_field': 'value1',
                'boolean_field': 'True',
                'float_field': '10.1',
                'integer_field': '10',
            },
        },
        sort_keys=True,
    )

    expected_input_job1 = json.dumps(
        {
            'job_id': 'job1',
            'job_type': 'JOB_1',
            'string_field': 'value1',
            'boolean_field': True,
            'float_field': 10.1,
            'integer_field': 10,
            'job_parameters': {
                'granules': [
                    'granule1',
                    'granule2',
                ],
                'string_field': 'value1',
                'boolean_field': True,
                'float_field': 10.1,
                'integer_field': 10,
            },
            'batch_job_parameters': {
                'string_field': 'value1',
                'boolean_field': 'True',
            },
        },
        sort_keys=True,
    )

    expected_input_job2 = json.dumps(
        {
            'job_id': 'job2',
            'job_type': 'JOB_2',
            'string_field': 'value1',
            'boolean_field': True,
            'float_field': 10.1,
            'integer_field': 10,
            'job_parameters': {
                'granules': [
                    'granule1',
                    'granule2',
                ],
                'string_field': 'value1',
                'boolean_field': True,
                'float_field': 10.1,
                'integer_field': 10,
            },
            'batch_job_parameters': {},
        },
        sort_keys=True,
    )

    with (
        patch('start_execution.STEP_FUNCTION.start_execution') as mock_start_execution,
        patch.dict(os.environ, {'STEP_FUNCTION_ARN': 'test-state-machine-arn'}, clear=True),
        patch('start_execution.BATCH_PARAMS_BY_JOB_TYPE', batch_params_by_job_type),
    ):
        start_execution.submit_jobs(jobs)

        assert mock_start_execution.mock_calls == [
            call(
                stateMachineArn='test-state-machine-arn',
                input=expected_input_job0,
                name='job0',
            ),
            call(
                stateMachineArn='test-state-machine-arn',
                input=expected_input_job1,
                name='job1',
            ),
            call(
                stateMachineArn='test-state-machine-arn',
                input=expected_input_job2,
                name='job2',
            ),
        ]


def test_lambda_handler():
    with (
        patch('dynamo.jobs.get_jobs_waiting_for_execution') as mock_get_jobs_waiting_for_execution,
        patch('dynamo.util.convert_decimals_to_numbers') as mock_convert_decimals_to_numbers,
        patch('start_execution.submit_jobs') as mock_submit_jobs,
    ):
        mock_get_jobs_waiting_for_execution.return_value = 'mock_jobs'
        mock_convert_decimals_to_numbers.return_value = 'converted_jobs'

        start_execution.lambda_handler({}, None)

        mock_get_jobs_waiting_for_execution.assert_called_once_with(limit=500)
        mock_convert_decimals_to_numbers.assert_called_once_with('mock_jobs')
        mock_submit_jobs.assert_called_once_with('converted_jobs')
