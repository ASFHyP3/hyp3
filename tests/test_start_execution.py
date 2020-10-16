from decimal import Decimal
from json import dumps
from os import environ, path

import boto3
import pytest
import yaml
from botocore.stub import Stubber
from moto import mock_dynamodb2
from start_execution import STEP_FUNCTION, submit_jobs, get_pending_jobs


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv('AWS_REGION', 'myRegion')
    monkeypatch.setenv('STEP_FUNCTION_ARN', 'myStepFunctionArn')
    monkeypatch.setenv('TABLE_NAME', 'jobsTable')


@pytest.fixture
def states_stubber():
    with Stubber(STEP_FUNCTION) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


@pytest.fixture
def job_table():
    with mock_dynamodb2():
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.create_table(
            TableName=environ['TABLE_NAME'],
            **get_table_properties_from_template('JobsTable'),
        )
        yield table


def get_table_properties_from_template(resource_name):
    yaml.SafeLoader.add_multi_constructor('!', lambda loader, suffix, node: None)
    template_file = path.join(path.dirname(__file__), '../apps/main-cf.yml')
    with open(template_file, 'r') as f:
        template = yaml.safe_load(f)
    table_properties = template['Resources'][resource_name]['Properties']
    return table_properties


def test_get_pending_jobs(job_table):
    assert get_pending_jobs() == []

    table_items = [
        {
            'job_id': 'job1',
            'user_id': 'user1',
            'status_code': 'FAILED',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
        {
            'job_id': 'job2',
            'user_id': 'user1',
            'status_code': 'PENDING',
            'request_time': '2000-01-02T00:00:00+00:00',
        },
        {
            'job_id': 'job3',
            'user_id': 'user1',
            'status_code': 'RUNNING',
            'request_time': '2000-01-03T00:00:00+00:00',
        },
    ]
    for item in table_items:
        job_table.put_item(Item=item)
    assert get_pending_jobs() == table_items[1:2]


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
