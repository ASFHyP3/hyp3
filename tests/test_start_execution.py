from decimal import Decimal
from json import dumps

import pytest
from botocore.stub import Stubber

from start_execution import STEP_FUNCTION, submit_jobs


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv('AWS_REGION', 'myRegion')
    monkeypatch.setenv('STEP_FUNCTION_ARN', 'myStepFunctionArn')


@pytest.fixture
def states_stubber():
    with Stubber(STEP_FUNCTION) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


def test_submit_jobs(states_stubber):
    jobs = [
          {
              'job_id': 'myJobId',
              'string_field': 'value1',
              'boolean_field': True,
              'decimal_float_field': Decimal('10.1'),
              'decimal_integer_field': Decimal('10'),
              'job_parameters': {
                  'granules': [
                      'granule1',
                      'granule2',
                  ],
                  'string_field': 'value1',
                  'boolean_field': True,
                  'decimal_float_field': Decimal('10.1'),
                  'decimal_integer_field': Decimal('10'),
              },
          },
    ]

    states_input = {
        'job_id': 'myJobId',
        'string_field': 'value1',
        'boolean_field': True,
        'decimal_float_field': 10.1,
        'decimal_integer_field': 10,
        'job_parameters': {
            'granules': 'granule1 granule2',
            'string_field': 'value1',
            'boolean_field': 'True',
            'decimal_float_field': '10.1',
            'decimal_integer_field': '10',
        },
    }

    states_stubber.add_response(
        method='start_execution',
        expected_params={
            'stateMachineArn': 'myStepFunctionArn',
            'name': 'myJobId',
            'input': dumps(states_input, sort_keys=True),
        },
        service_response={
            'executionArn': 'myExecutionArn',
            'startDate': '2020-01-01',
        },
    )

    submit_jobs(jobs)
