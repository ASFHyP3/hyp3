import json
import os
from unittest.mock import call, patch

import start_execution_worker


def test_convert_to_string():
    assert start_execution_worker.convert_to_string(1) == '1'
    assert start_execution_worker.convert_to_string(True) == 'True'
    assert start_execution_worker.convert_to_string([1, 2]) == '1 2'
    assert start_execution_worker.convert_to_string(['abc', 'bcd']) == 'abc bcd'
    assert start_execution_worker.convert_to_string('abc') == 'abc'


def test_convert_parameters_to_string():
    parameters = {
        'param1': 1,
        'param2': True,
        'param3': [1, 2],
        'param4': ['abc', 'bcd'],
        'param5': 'abc',
    }
    assert start_execution_worker.convert_parameters_to_strings(parameters) == {
        'param1': '1',
        'param2': 'True',
        'param3': '1 2',
        'param4': 'abc bcd',
        'param5': 'abc',
    }


def test_submit_jobs():
    jobs = [
        {
            'job_id': 'job0',
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
            'job_parameters': {'granules': ['granule1']},
        }
    ]

    expected_input_job0 = json.dumps(
        {
            'job_id': 'job0',
            'string_field': 'value1',
            'boolean_field': True,
            'float_field': 10.1,
            'integer_field': 10,
            'job_parameters': {
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
            'job_parameters': {'granules': 'granule1'},
        },
        sort_keys=True,
    )

    with patch('start_execution_worker.STEP_FUNCTION.start_execution') as mock_start_execution, \
            patch.dict(os.environ, {'STEP_FUNCTION_ARN': 'test-state-machine-arn'}, clear=True):
        start_execution_worker.submit_jobs(jobs)

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
            )
        ]


def test_lambda_handler():
    with patch('start_execution_worker.submit_jobs') as mock_submit_jobs:
        start_execution_worker.lambda_handler({'jobs': [1, 2, 3]}, None)

        assert mock_submit_jobs.mock_calls == [call([1, 2, 3])]
