from datetime import date

import pytest

import scale_cluster
from botocore.stub import Stubber


@pytest.fixture
def batch_stubber():
    with Stubber(scale_cluster.BATCH) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


@pytest.fixture
def cost_explorer_stubber():
    with Stubber(scale_cluster.COST_EXPLORER) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


def test_get_time_period():
    result = scale_cluster.get_time_period(date(year=2020, month=1, day=1))
    assert result == {'Start': '2020-01-01', 'End': '2020-02-01'}

    result = scale_cluster.get_time_period(date(year=2020, month=12, day=31))
    assert result == {'Start': '2020-12-01', 'End': '2021-01-01'}

    result = scale_cluster.get_time_period(date(year=2020, month=12, day=1))
    assert result == {'Start': '2020-12-01', 'End': '2021-01-01'}

    result = scale_cluster.get_time_period(date(year=2020, month=2, day=29))
    assert result == {'Start': '2020-02-01', 'End': '2020-03-01'}


def test_get_target_max_vcpus():
    vcpus = scale_cluster.get_target_max_vcpus(
        today=date(2020, 1, 1),
        monthly_budget=1000,
        month_to_date_spending=0,
        default_max_vcpus=1,
        expanded_max_vcpus=2,
        required_surplus=1000,
    )
    assert vcpus == 1

    vcpus = scale_cluster.get_target_max_vcpus(
        today=date(2020, 1, 31),
        monthly_budget=1000,
        month_to_date_spending=0,
        default_max_vcpus=3,
        expanded_max_vcpus=4,
        required_surplus=1000,
    )
    assert vcpus == 4

    vcpus = scale_cluster.get_target_max_vcpus(
        today=date(2020, 1, 31),
        monthly_budget=1000,
        month_to_date_spending=999.99,
        default_max_vcpus=1,
        expanded_max_vcpus=2,
        required_surplus=1000,
    )
    assert vcpus == 1

    vcpus = scale_cluster.get_target_max_vcpus(
        today=date(2020, 1, 31),
        monthly_budget=0,
        month_to_date_spending=0,
        default_max_vcpus=1,
        expanded_max_vcpus=2,
        required_surplus=1,
    )
    assert vcpus == 1

    vcpus = scale_cluster.get_target_max_vcpus(
        today=date(2020, 2, 20),
        monthly_budget=29000,
        month_to_date_spending=19001,
        default_max_vcpus=1,
        expanded_max_vcpus=2,
        required_surplus=1000,
    )
    assert vcpus == 1

    vcpus = scale_cluster.get_target_max_vcpus(
        today=date(2020, 2, 20),
        monthly_budget=29000,
        month_to_date_spending=19000,
        default_max_vcpus=1,
        expanded_max_vcpus=2,
        required_surplus=1000,
    )
    assert vcpus == 2

    vcpus = scale_cluster.get_target_max_vcpus(
        today=date(2020, 2, 20),
        monthly_budget=29000,
        month_to_date_spending=19000,
        default_max_vcpus=1,
        expanded_max_vcpus=2,
        required_surplus=1001,
    )
    assert vcpus == 1


def test_get_current_desired_vcpus(batch_stubber):
    expected_params = {'computeEnvironments': ['foo']}
    service_response = {
        'computeEnvironments': [
            {
                'computeEnvironmentName': 'environment name',
                'computeEnvironmentArn': 'environment arn',
                'ecsClusterArn': 'cluster arn',
                'computeResources': {
                    'type': 'MANAGED',
                    'desiredvCpus': 5,
                    'maxvCpus': 10,
                    'subnets': ['subnet1', 'subnet2'],
                },
            },
        ]
    }
    batch_stubber.add_response(
        method='describe_compute_environments', expected_params=expected_params, service_response=service_response
    )

    assert scale_cluster.get_current_desired_vcpus('foo') == 5


def test_set_max_vcpus(batch_stubber):
    expected_params = {'computeEnvironment': 'foo', 'computeResources': {'maxvCpus': 10}, 'state': 'ENABLED'}
    batch_stubber.add_response(
        method='update_compute_environment', expected_params=expected_params, service_response={}
    )
    scale_cluster.set_max_vcpus(compute_environment_arn='foo', target_max_vcpus=10, current_desired_vcpus=10)

    expected_params = {'computeEnvironment': 'foo', 'state': 'DISABLED'}
    batch_stubber.add_response(
        method='update_compute_environment', expected_params=expected_params, service_response={}
    )
    scale_cluster.set_max_vcpus(compute_environment_arn='foo', target_max_vcpus=10, current_desired_vcpus=11)


def test_get_month_to_date_spending(cost_explorer_stubber):
    expected_params = {
        'Metrics': ['UnblendedCost'],
        'Granularity': 'MONTHLY',
        'TimePeriod': {
            'Start': '2022-07-01',
            'End': '2022-08-01',
        },
    }
    mock_service_response = {
        'ResultsByTime': [
            {
                'Total': {
                    'UnblendedCost': {
                        'Amount': '100.2',
                    },
                },
            },
        ],
    }
    cost_explorer_stubber.add_response(
        method='get_cost_and_usage', expected_params=expected_params, service_response=mock_service_response
    )

    assert scale_cluster.get_month_to_date_spending(date(2022, 7, 15)) == 100.2
