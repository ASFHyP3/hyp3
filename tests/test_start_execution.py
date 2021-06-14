from decimal import Decimal
from json import dumps
from os import environ

import pytest
from botocore.stub import Stubber
from moto import mock_dynamodb2

from start_execution import DB, STEP_FUNCTION, get_pending_jobs, submit_jobs


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv('AWS_REGION', 'myRegion')
    monkeypatch.setenv('STEP_FUNCTION_ARN', 'myStepFunctionArn')
    monkeypatch.setenv('TABLE_NAME', 'myTableName')


@pytest.fixture
def states_stubber():
    with Stubber(STEP_FUNCTION) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


@pytest.fixture
def jobs_table(table_properties):
    with mock_dynamodb2():
        jobs_table = DB.create_table(
            TableName=environ['TABLE_NAME'],
            **table_properties['JobsTable'],
        )
        yield jobs_table


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


def test_get_pending_jobs(jobs_table):
    items = [
        {
            'job_id': 'job1',
            'status_code': 'RUNNING',
        },
        {
            'job_id': 'job2',
            'status_code': 'PENDING',
        },
        {
            'job_id': 'job3',
            'status_code': 'PENDING',
        },
        {
            'job_id': 'job4',
            'status_code': 'FAILED',
        },
    ]
    for item in items:
        jobs_table.put_item(Item=item)

    pending_jobs = get_pending_jobs(limit=1)
    assert pending_jobs == items[1:2]

    pending_jobs = get_pending_jobs(limit=2)
    assert pending_jobs == items[1:3]

    pending_jobs = get_pending_jobs(limit=3)
    assert pending_jobs == items[1:3]
