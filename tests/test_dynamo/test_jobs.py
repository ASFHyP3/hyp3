import unittest.mock
from decimal import Decimal

import pytest

import dynamo
from conftest import list_have_same_elements
from dynamo.exceptions import (
    InsufficientCreditsError,
    InvalidApplicationStatusError,
    NotStartedApplicationError,
    PatchJobDifferentUserError,
    PendingApplicationError,
    RejectedApplicationError,
)
from dynamo.user import APPLICATION_APPROVED
from dynamo.util import current_utc_time


def test_query_jobs_by_user(tables):
    table_items = [
        {
            'job_id': 'job1',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
        {
            'job_id': 'job2',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
        {
            'job_id': 'job3',
            'user_id': 'user2',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
    ]
    for item in table_items:
        tables.jobs_table.put_item(Item=item)

    response, next_key = dynamo.jobs.query_jobs('user1')

    assert next_key is None
    assert len(response) == 2
    assert list_have_same_elements(response, table_items[:2])


def test_query_jobs_by_time(tables):
    table_items = [
        {
            'job_id': 'job1',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
        {
            'job_id': 'job2',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-02T00:00:00+00:00',
        },
        {
            'job_id': 'job3',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-03T00:00:00+00:00',
        },
    ]
    for item in table_items:
        tables.jobs_table.put_item(Item=item)

    start = '2000-01-01T00:00:00z'
    end = '2000-01-03T00:00:00z'
    response, _ = dynamo.jobs.query_jobs('user1', start, end)
    assert len(response) == 3
    assert response == list(reversed(table_items))

    start = '2000-01-01T00:00:01z'
    end = '2000-01-02T00:59:59z'
    response, _ = dynamo.jobs.query_jobs('user1', start, end)
    assert len(response) == 1
    assert list_have_same_elements(response, table_items[1:2])

    start = '2000-01-01T00:00:01z'
    response, _ = dynamo.jobs.query_jobs('user1', start, None)
    assert len(response) == 2
    assert list_have_same_elements(response, table_items[1:])

    end = '2000-01-02T00:59:59z'
    response, _ = dynamo.jobs.query_jobs('user1', None, end)
    assert len(response) == 2
    assert list_have_same_elements(response, table_items[:2])


def test_query_jobs_by_status(tables):
    table_items = [
        {
            'job_id': 'job1',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
        {
            'job_id': 'job2',
            'user_id': 'user1',
            'status_code': 'status2',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
        {
            'job_id': 'job3',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
    ]
    for item in table_items:
        tables.jobs_table.put_item(Item=item)

    response, _ = dynamo.jobs.query_jobs('user1', status_code='status1')
    assert len(response) == 2
    assert list_have_same_elements(response, table_items[0::2])


def test_query_jobs_by_name(tables):
    table_items = [
        {
            'job_id': 'job1',
            'name': 'name1',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
        {
            'job_id': 'job2',
            'name': 'name1',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
        {
            'job_id': 'job3',
            'name': 'name2',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
    ]
    for item in table_items:
        tables.jobs_table.put_item(Item=item)

    response, _ = dynamo.jobs.query_jobs('user1', name='name1')
    assert len(response) == 2
    assert list_have_same_elements(response, table_items[:2])


def test_query_jobs_by_type(tables):
    table_items = [
        {
            'job_id': 'job1',
            'job_type': 'RTC_GAMMA',
            'name': 'name1',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
        {
            'job_id': 'job2',
            'job_type': 'RTC_GAMMA',
            'name': 'name1',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
        {
            'job_id': 'job3',
            'job_type': 'INSAR_GAMMA',
            'name': 'name2',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
    ]
    for item in table_items:
        tables.jobs_table.put_item(Item=item)

    response, _ = dynamo.jobs.query_jobs('user1', job_type='RTC_GAMMA')
    assert len(response) == 2
    assert list_have_same_elements(response, table_items[:2])


def test_get_credit_cost():
    costs: dict = {
        'RTC_GAMMA': {
            'cost_parameters': ['resolution'],
            'cost_table': {
                '10': Decimal(60.0),
                '20': Decimal(15.0),
                '30': Decimal(5.0),
            },
        },
        'INSAR_ISCE_BURST': {'cost': Decimal(1.0)},
        'INSAR_ISCE_MULTI_BURST': {
            'cost_parameters': ['looks', 'reference'],
            'cost_table': {
                '5x1': {
                    '1': Decimal(1.0),
                    '2': Decimal(1.0),
                    '3': Decimal(10.0),
                }
            },
        },
    }
    assert (
        dynamo.jobs._get_credit_cost({'job_type': 'RTC_GAMMA', 'job_parameters': {'resolution': 10.0}}, costs) == 60.0
    )
    assert (
        dynamo.jobs._get_credit_cost({'job_type': 'RTC_GAMMA', 'job_parameters': {'resolution': 20.0}}, costs) == 15.0
    )
    assert dynamo.jobs._get_credit_cost({'job_type': 'RTC_GAMMA', 'job_parameters': {'resolution': 30.0}}, costs) == 5.0
    with pytest.raises(ValueError, match=r'^Cost not found for job type RTC_GAMMA with resolution == 13$'):
        dynamo.jobs._get_credit_cost({'job_type': 'RTC_GAMMA', 'job_parameters': {'resolution': 13.0}}, costs)
    assert (
        dynamo.jobs._get_credit_cost({'job_type': 'INSAR_ISCE_BURST', 'job_parameters': {'foo': 'bar'}}, costs) == 1.0
    )
    assert dynamo.jobs._get_credit_cost({'job_type': 'INSAR_ISCE_BURST', 'job_parameters': {}}, costs) == 1.0
    multi_burst_job = {
        'job_type': 'INSAR_ISCE_MULTI_BURST',
        'job_parameters': {'reference': ['g1', 'g2', 'g3'], 'looks': '5x1'},
    }
    assert dynamo.jobs._get_credit_cost(multi_burst_job, costs) == 10.0
    multi_burst_job = {
        'job_type': 'INSAR_ISCE_MULTI_BURST',
        'job_parameters': {'reference': ['g1', 'g2'], 'looks': '5x1'},
    }
    assert dynamo.jobs._get_credit_cost(multi_burst_job, costs) == 1.0
    multi_burst_job = {
        'job_type': 'INSAR_ISCE_MULTI_BURST',
        'job_parameters': {'reference': ['g1'], 'looks': '5x1'},
    }
    assert dynamo.jobs._get_credit_cost(multi_burst_job, costs) == 1.0


def test_nested_credit_cost_lookup():
    costs = {
        'myJob': {
            'cost_parameters': ['option1', 'option2', 'option3'],
            'cost_table': {
                'a': {
                    'x': {'1': Decimal(11), '2': Decimal(21)},
                    'y': {'1': Decimal(12), '2': Decimal(22)},
                    'z': {'1': Decimal(13), '2': Decimal(23)},
                },
                'b': {
                    'x': {'1': Decimal(14), '2': Decimal(24)},
                    'y': {'1': Decimal(15), '2': Decimal(25)},
                    'z': {'1': Decimal(16), '2': Decimal(26)},
                },
                'c': {
                    'x': {'1': Decimal(17), '2': Decimal(27)},
                    'y': {'1': Decimal(18), '2': Decimal(28)},
                    'z': {'1': Decimal(19), '2': Decimal(29)},
                },
            },
        }
    }

    job = {'job_type': 'myJob', 'job_parameters': {'option1': 'c', 'option2': 'x', 'option3': 1}}
    assert dynamo.jobs._get_credit_cost(job, costs) == 17.0

    job = {'job_type': 'myJob', 'job_parameters': {'option1': 'b', 'option2': 'z', 'option3': 1}}
    assert dynamo.jobs._get_credit_cost(job, costs) == 16.0

    job = {'job_type': 'myJob', 'job_parameters': {'option1': 'a', 'option2': 'y', 'option3': 2}}
    assert dynamo.jobs._get_credit_cost(job, costs) == 22.0


def test_get_credit_cost_validate_keys():
    costs: dict = {
        'JOB_TYPE_A': {'cost_parameters': ['foo'], 'cost_table': {'bar': Decimal(3.0)}},
        'JOB_TYPE_B': {'cost': Decimal(5.0)},
        'JOB_TYPE_C': {'cost_parameters': ['']},
        'JOB_TYPE_D': {'cost_table': {}},
        'JOB_TYPE_E': {'cost_parameters': [''], 'cost_table': {}, 'cost': Decimal(1.0)},
        'JOB_TYPE_F': {'cost_parameters': [''], 'cost_table': {}, 'foo': None},
        'JOB_TYPE_G': {'cost': 5.0},
        'JOB_TYPE_H': {'cost_parameters': ['foo'], 'cost_table': {(1, 2): Decimal(3.0)}},
    }

    assert dynamo.jobs._get_credit_cost({'job_type': 'JOB_TYPE_A', 'job_parameters': {'foo': 'bar'}}, costs) == 3.0
    assert dynamo.jobs._get_credit_cost({'job_type': 'JOB_TYPE_B'}, costs) == 5.0

    with pytest.raises(ValueError, match=r'^Cost definition for job type JOB_TYPE_C has invalid keys.*'):
        dynamo.jobs._get_credit_cost({'job_type': 'JOB_TYPE_C'}, costs)
    with pytest.raises(ValueError, match=r'^Cost definition for job type JOB_TYPE_D has invalid keys.*'):
        dynamo.jobs._get_credit_cost({'job_type': 'JOB_TYPE_D'}, costs)
    with pytest.raises(ValueError, match=r'^Cost definition for job type JOB_TYPE_E has invalid keys.*'):
        dynamo.jobs._get_credit_cost({'job_type': 'JOB_TYPE_E'}, costs)
    with pytest.raises(ValueError, match=r'^Cost definition for job type JOB_TYPE_F has invalid keys.*'):
        dynamo.jobs._get_credit_cost({'job_type': 'JOB_TYPE_F'}, costs)
    with pytest.raises(ValueError, match=r'^Job type JOB_TYPE_G has non-Decimal cost value.*'):
        dynamo.jobs._get_credit_cost({'job_type': 'JOB_TYPE_G'}, costs)

    error_match = r"^Cost parameter foo for job type JOB_TYPE_H has unsupported type <class 'tuple'>"
    with pytest.raises(ValueError, match=error_match):
        dynamo.jobs._get_credit_cost({'job_type': 'JOB_TYPE_H', 'job_parameters': {'foo': (1, 2)}}, costs)


def test_put_jobs(tables, monkeypatch, approved_user):
    monkeypatch.setenv('DEFAULT_CREDITS_PER_USER', '10')
    payload = [{'name': 'name1'}, {'name': 'name1'}, {'name': 'name2'}]

    with unittest.mock.patch('dynamo.user._get_current_month') as mock_get_current_month:
        mock_get_current_month.return_value = '2024-02'

        jobs = dynamo.jobs.put_jobs(approved_user, payload)

        mock_get_current_month.assert_called_once_with()

    assert len(jobs) == 3
    for job in jobs:
        assert set(job.keys()) == {
            'name',
            'job_id',
            'user_id',
            'status_code',
            'execution_started',
            'request_time',
            'priority',
            'credit_cost',
        }
        assert job['request_time'] <= current_utc_time()
        assert job['user_id'] == approved_user
        assert job['status_code'] == 'PENDING'
        assert job['execution_started'] is False
        assert job['credit_cost'] == 1

    assert tables.jobs_table.scan()['Items'] == sorted(jobs, key=lambda item: item['job_id'])

    assert tables.users_table.scan()['Items'] == [
        {
            'user_id': approved_user,
            'remaining_credits': Decimal(7),
            '_month_of_last_credit_reset': '2024-02',
            'application_status': APPLICATION_APPROVED,
        }
    ]


def test_put_jobs_application_status(tables):
    payload = [{'name': 'name1'}, {'name': 'name1'}, {'name': 'name2'}]

    tables.users_table.put_item(
        Item={
            'user_id': 'foo',
            'remaining_credits': Decimal(0),
            'application_status': dynamo.user.APPLICATION_NOT_STARTED,
        }
    )
    with pytest.raises(NotStartedApplicationError):
        dynamo.jobs.put_jobs('foo', payload)
    assert tables.jobs_table.scan()['Items'] == []

    tables.users_table.put_item(
        Item={
            'user_id': 'foo',
            'remaining_credits': Decimal(0),
            'application_status': dynamo.user.APPLICATION_PENDING,
        }
    )
    with pytest.raises(PendingApplicationError):
        dynamo.jobs.put_jobs('foo', payload)
    assert tables.jobs_table.scan()['Items'] == []

    tables.users_table.put_item(
        Item={
            'user_id': 'foo',
            'remaining_credits': Decimal(0),
            'application_status': dynamo.user.APPLICATION_REJECTED,
        }
    )
    with pytest.raises(RejectedApplicationError):
        dynamo.jobs.put_jobs('foo', payload)
    assert tables.jobs_table.scan()['Items'] == []

    tables.users_table.put_item(
        Item={
            'user_id': 'foo',
            'remaining_credits': Decimal(0),
            'application_status': 'bar',
        }
    )
    with pytest.raises(InvalidApplicationStatusError):
        dynamo.jobs.put_jobs('foo', payload)
    assert tables.jobs_table.scan()['Items'] == []


def test_put_jobs_default_params(tables, approved_user):
    default_params = {
        'JOB_TYPE_A': {'a1': 'a1_default', 'a2': 'a2_default'},
        'JOB_TYPE_B': {'b1': 'b1_default'},
        'JOB_TYPE_C': {},
    }
    costs = {
        'JOB_TYPE_A': {'cost': Decimal('1.0')},
        'JOB_TYPE_B': {'cost': Decimal('1.0')},
        'JOB_TYPE_C': {'cost': Decimal('1.0')},
    }
    payload: list[dict] = [
        {},
        {'job_type': 'JOB_TYPE_A'},
        {'job_type': 'JOB_TYPE_A', 'job_parameters': {}},
        {'job_type': 'JOB_TYPE_A', 'job_parameters': {'a1': 'foo'}},
        {'job_type': 'JOB_TYPE_A', 'job_parameters': {'a1': 'foo', 'a2': 'bar'}},
        {'job_type': 'JOB_TYPE_B', 'job_parameters': {}},
        {'job_type': 'JOB_TYPE_B', 'job_parameters': {'b1': 'foo'}},
        {'job_type': 'JOB_TYPE_B', 'job_parameters': {'b1': 'foo', 'b2': 'bar'}},
        {'job_type': 'JOB_TYPE_C'},
        {'job_type': 'JOB_TYPE_C', 'job_parameters': {}},
        {'job_type': 'JOB_TYPE_C', 'job_parameters': {'c1': 'foo'}},
        {'job_parameters': {'n1': 'foo'}},
    ]
    with (
        unittest.mock.patch('dynamo.jobs.DEFAULT_PARAMS_BY_JOB_TYPE', default_params),
        unittest.mock.patch('dynamo.jobs.COSTS', costs),
    ):
        jobs = dynamo.jobs.put_jobs(approved_user, payload)

    assert 'job_parameters' not in jobs[0]
    assert jobs[1]['job_parameters'] == {'a1': 'a1_default', 'a2': 'a2_default'}
    assert jobs[2]['job_parameters'] == {'a1': 'a1_default', 'a2': 'a2_default'}
    assert jobs[3]['job_parameters'] == {'a1': 'foo', 'a2': 'a2_default'}
    assert jobs[4]['job_parameters'] == {'a1': 'foo', 'a2': 'bar'}
    assert jobs[5]['job_parameters'] == {'b1': 'b1_default'}
    assert jobs[6]['job_parameters'] == {'b1': 'foo'}
    assert jobs[7]['job_parameters'] == {'b1': 'foo', 'b2': 'bar'}
    assert jobs[8]['job_parameters'] == {}
    assert jobs[9]['job_parameters'] == {}
    assert jobs[10]['job_parameters'] == {'c1': 'foo'}
    assert jobs[11]['job_parameters'] == {'n1': 'foo'}

    assert tables.jobs_table.scan()['Items'] == sorted(jobs, key=lambda item: item['job_id'])


def test_put_jobs_costs(tables, monkeypatch, approved_user):
    monkeypatch.setenv('DEFAULT_CREDITS_PER_USER', '100')

    costs = {
        'RTC_GAMMA': {
            'cost_parameters': ['resolution'],
            'cost_table': {
                '30': Decimal('5.0'),
                '20': Decimal('15.0'),
                '10': Decimal('60.0'),
            },
        },
        'INSAR_ISCE_BURST': {
            'cost_parameters': ['looks'],
            'cost_table': {
                '20x4': Decimal('0.4'),
                '10x2': Decimal('0.7'),
                '5x1': Decimal('1.8'),
            },
        },
    }
    default_params = {
        'RTC_GAMMA': {'resolution': 30},
        'INSAR_ISCE_BURST': {'looks': '20x4'},
    }
    payload = [
        {'job_type': 'RTC_GAMMA', 'job_parameters': {'resolution': 30}},
        {'job_type': 'RTC_GAMMA', 'job_parameters': {'resolution': 20}},
        {'job_type': 'RTC_GAMMA', 'job_parameters': {'resolution': 10}},
        {'job_type': 'INSAR_ISCE_BURST', 'job_parameters': {'looks': '20x4'}},
        {'job_type': 'INSAR_ISCE_BURST', 'job_parameters': {'looks': '10x2'}},
        {'job_type': 'INSAR_ISCE_BURST', 'job_parameters': {'looks': '5x1'}},
        {'job_type': 'RTC_GAMMA', 'job_parameters': {}},
        {'job_type': 'INSAR_ISCE_BURST', 'job_parameters': {}},
    ]
    with (
        unittest.mock.patch('dynamo.jobs.COSTS', costs),
        unittest.mock.patch('dynamo.jobs.DEFAULT_PARAMS_BY_JOB_TYPE', default_params),
    ):
        jobs = dynamo.jobs.put_jobs(approved_user, payload)

    assert len(jobs) == 8

    assert jobs[0]['priority'] == 100
    assert jobs[1]['priority'] == 95
    assert jobs[2]['priority'] == 80
    assert jobs[3]['priority'] == 20
    assert jobs[4]['priority'] == 20
    assert jobs[5]['priority'] == 19
    assert jobs[6]['priority'] == 17
    assert jobs[7]['priority'] == 12

    assert jobs[0]['credit_cost'] == Decimal('5.0')
    assert jobs[1]['credit_cost'] == Decimal('15.0')
    assert jobs[2]['credit_cost'] == Decimal('60.0')
    assert jobs[3]['credit_cost'] == Decimal('0.4')
    assert jobs[4]['credit_cost'] == Decimal('0.7')
    assert jobs[5]['credit_cost'] == Decimal('1.8')
    assert jobs[6]['credit_cost'] == Decimal('5.0')
    assert jobs[7]['credit_cost'] == Decimal('0.4')

    assert tables.jobs_table.scan()['Items'] == sorted(jobs, key=lambda item: item['job_id'])
    assert tables.users_table.scan()['Items'][0]['remaining_credits'] == Decimal('11.7')


def test_put_jobs_insufficient_credits(tables, monkeypatch, approved_user):
    monkeypatch.setenv('DEFAULT_CREDITS_PER_USER', '1')
    payload = [{'name': 'name1'}, {'name': 'name2'}]

    with pytest.raises(InsufficientCreditsError):
        dynamo.jobs.put_jobs(approved_user, payload)

    assert tables.jobs_table.scan()['Items'] == []
    assert tables.users_table.scan()['Items'][0]['remaining_credits'] == 1


def test_put_jobs_infinite_credits(tables, monkeypatch):
    monkeypatch.setenv('DEFAULT_CREDITS_PER_USER', '1')
    payload = [{'name': 'name1'}, {'name': 'name2'}]

    tables.users_table.put_item(
        Item={'user_id': 'user1', 'remaining_credits': None, 'application_status': APPLICATION_APPROVED}
    )

    jobs = dynamo.jobs.put_jobs('user1', payload)

    assert len(jobs) == 2
    for job in jobs:
        assert job['priority'] == 0


def test_put_jobs_priority_override(tables):
    payload = [{'name': 'name1'}, {'name': 'name2'}]
    user = {
        'user_id': 'user1',
        'priority_override': 100,
        'remaining_credits': 3,
        'application_status': APPLICATION_APPROVED,
    }
    tables.users_table.put_item(Item=user)

    jobs = dynamo.jobs.put_jobs('user1', payload)

    assert len(jobs) == 2
    for job in jobs:
        assert job['priority'] == 100

    user = {
        'user_id': 'user1',
        'priority_override': 550,
        'remaining_credits': None,
        'application_status': APPLICATION_APPROVED,
    }
    tables.users_table.put_item(Item=user)

    jobs = dynamo.jobs.put_jobs('user1', payload)

    assert len(jobs) == 2
    for job in jobs:
        assert job['priority'] == 550


def test_put_jobs_priority(tables, monkeypatch, approved_user):
    monkeypatch.setenv('DEFAULT_CREDITS_PER_USER', '7')

    jobs = dynamo.jobs.put_jobs(user_id=approved_user, jobs=[{}, {}, {}])
    assert jobs[0]['priority'] == 7
    assert jobs[1]['priority'] == 6
    assert jobs[2]['priority'] == 5

    jobs.extend(dynamo.jobs.put_jobs(user_id=approved_user, jobs=[{}, {}, {}, {}]))
    assert jobs[3]['priority'] == 4
    assert jobs[4]['priority'] == 3
    assert jobs[5]['priority'] == 2
    assert jobs[6]['priority'] == 1


def test_put_jobs_priority_extra_credits(tables, monkeypatch, approved_user):
    monkeypatch.setenv('DEFAULT_CREDITS_PER_USER', '10003')

    jobs = dynamo.jobs.put_jobs(user_id=approved_user, jobs=[{}])
    assert jobs[0]['priority'] == 9999

    jobs.extend(dynamo.jobs.put_jobs(user_id=approved_user, jobs=[{}]))
    assert jobs[1]['priority'] == 9999

    jobs.extend(dynamo.jobs.put_jobs(user_id=approved_user, jobs=[{}] * 6))
    assert jobs[2]['priority'] == 9999
    assert jobs[3]['priority'] == 9999
    assert jobs[4]['priority'] == 9999
    assert jobs[5]['priority'] == 9998
    assert jobs[6]['priority'] == 9997
    assert jobs[7]['priority'] == 9996


def test_put_jobs_decrement_credits_failure(tables, approved_user):
    with unittest.mock.patch('dynamo.user.decrement_credits') as mock_decrement_credits:
        mock_decrement_credits.side_effect = Exception('test error')
        with pytest.raises(Exception, match=r'^test error$'):
            dynamo.jobs.put_jobs(approved_user, [{'name': 'job1'}])

    assert tables.jobs_table.scan()['Items'] == []


def test_get_job(tables):
    table_items = [
        {
            'job_id': 'job1',
            'name': 'name1',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
        {
            'job_id': 'job2',
            'name': 'name2',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
        {
            'job_id': 'job3',
            'name': 'name3',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
    ]
    for item in table_items:
        tables.jobs_table.put_item(Item=item)

    assert dynamo.jobs.get_job('job1') == table_items[0]
    assert dynamo.jobs.get_job('job2') == table_items[1]
    assert dynamo.jobs.get_job('job3') == table_items[2]
    assert dynamo.jobs.get_job('foo') is None


def test_query_jobs_sort_order(tables):
    table_items = [
        {
            'job_id': 'job1',
            'job_type': 'RTC_GAMMA',
            'name': 'name1',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-03T00:00:00+00:00',
        },
        {
            'job_id': 'job2',
            'job_type': 'RTC_GAMMA',
            'name': 'name1',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-02T00:00:00+00:00',
        },
        {
            'job_id': 'job3',
            'job_type': 'INSAR_GAMMA',
            'name': 'name2',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
    ]
    for item in [table_items[2], table_items[0], table_items[1]]:
        tables.jobs_table.put_item(Item=item)

    response, _ = dynamo.jobs.query_jobs('user1')
    assert response == table_items


def test_update_job(tables):
    table_items = [
        {
            'job_id': 'job1',
            'name': 'name1',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
    ]
    for item in table_items:
        tables.jobs_table.put_item(Item=item)

    job = {'job_id': 'job1', 'status_code': 'status2', 'processing_time_in_seconds': 1.23}
    dynamo.jobs.update_job(job)

    response = tables.jobs_table.scan()
    expected_response = [
        {
            'job_id': 'job1',
            'name': 'name1',
            'user_id': 'user1',
            'status_code': 'status2',
            'request_time': '2000-01-01T00:00:00+00:00',
            'processing_time_in_seconds': Decimal('1.23'),
        },
    ]
    assert response['Items'] == expected_response


def test_patch_job(tables):
    table_items = [
        {
            'job_id': 'job1',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': 'job2',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user2',
        },
    ]
    for item in table_items:
        tables.jobs_table.put_item(Item=item)

    assert dynamo.jobs.patch_job('job1', 'newname', 'user1') == {
        'job_id': 'job1',
        'name': 'newname',
        'somefield': 'somevalue',
        'user_id': 'user1',
    }
    assert tables.jobs_table.scan()['Items'] == [
        {
            'job_id': 'job1',
            'name': 'newname',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': 'job2',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user2',
        },
    ]

    assert dynamo.jobs.patch_job('job1', None, 'user1') == {
        'job_id': 'job1',
        'somefield': 'somevalue',
        'user_id': 'user1',
    }
    assert tables.jobs_table.scan()['Items'] == [
        {
            'job_id': 'job1',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': 'job2',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user2',
        },
    ]


def test_patch_job_different_user(tables):
    table_items = [
        {
            'job_id': 'job1',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': 'job2',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user2',
        },
    ]
    for item in table_items:
        tables.jobs_table.put_item(Item=item)

    with pytest.raises(PatchJobDifferentUserError, match=r'^You cannot modify a different user\'s job$'):
        dynamo.jobs.patch_job('job2', 'newname', 'user1')

    with pytest.raises(PatchJobDifferentUserError, match=r'^You cannot modify a different user\'s job$'):
        dynamo.jobs.patch_job('job2', None, 'user1')

    assert tables.jobs_table.scan()['Items'] == [
        {
            'job_id': 'job1',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': 'job2',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user2',
        },
    ]


def test_get_jobs_waiting_for_execution(tables):
    items = [
        {'job_id': 'job0', 'status_code': 'PENDING', 'execution_started': False},
        {'job_id': 'job1', 'status_code': 'PENDING'},
        {'job_id': 'job2', 'status_code': 'RUNNING', 'execution_started': True},
        {'job_id': 'job3', 'status_code': 'PENDING', 'execution_started': True},
        {'job_id': 'job4', 'status_code': 'PENDING', 'execution_started': False},
        {'job_id': 'job5', 'status_code': 'PENDING', 'execution_started': True},
        {'job_id': 'job6', 'status_code': 'PENDING', 'execution_started': False},
        {'job_id': 'job7', 'status_code': 'PENDING', 'execution_started': True},
        {'job_id': 'job8', 'status_code': 'RUNNING'},
        {'job_id': 'job9', 'status_code': 'PENDING'},
    ]
    for item in items:
        tables.jobs_table.put_item(Item=item)

    assert dynamo.jobs.get_jobs_waiting_for_execution(limit=1) == [items[0]]
    assert dynamo.jobs.get_jobs_waiting_for_execution(limit=2) == [items[0], items[1]]
    assert dynamo.jobs.get_jobs_waiting_for_execution(limit=3) == [items[0], items[1], items[4]]
    assert dynamo.jobs.get_jobs_waiting_for_execution(limit=4) == [items[0], items[1], items[4], items[6]]
    assert dynamo.jobs.get_jobs_waiting_for_execution(limit=5) == [items[0], items[1], items[4], items[6], items[9]]
    assert dynamo.jobs.get_jobs_waiting_for_execution(limit=6) == [items[0], items[1], items[4], items[6], items[9]]


def test_decimal_conversion(tables):
    table_items = [
        {
            'job_id': 'job1',
            'job_type': 'RTC_GAMMA',
            'name': 'name1',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-03T00:00:00+00:00',
            'float_value': 30.04,
        },
        {
            'job_id': 'job2',
            'job_type': 'RTC_GAMMA',
            'name': 'name1',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-02T00:00:00+00:00',
            'float_value': 0.0,
        },
        {
            'job_id': 'job3',
            'job_type': 'INSAR_GAMMA',
            'name': 'name2',
            'user_id': 'user1',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
            'float_value': 0.1,
        },
    ]
    for item in table_items:
        tables.jobs_table.put_item(Item=dynamo.util.convert_floats_to_decimals(item))

    response, _ = dynamo.jobs.query_jobs('user1')
    assert response[0]['float_value'] == Decimal('30.04')
    assert response[1]['float_value'] == Decimal('0.0')
    assert response[2]['float_value'] == Decimal('0.1')
