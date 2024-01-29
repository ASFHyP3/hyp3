import os
import unittest.mock
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from conftest import list_have_same_elements

import dynamo


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


def test_put_jobs(tables, monkeypatch):
    monkeypatch.setenv('DEFAULT_CREDITS_PER_USER', '10')
    payload = [{'name': 'name1'}, {'name': 'name1'}, {'name': 'name2'}]

    with unittest.mock.patch('dynamo.user._get_current_month') as mock_get_current_month:
        mock_get_current_month.return_value = '2024-02'

        jobs = dynamo.jobs.put_jobs('user1', payload)

        mock_get_current_month.assert_called_once_with()

    assert len(jobs) == 3
    for job in jobs:
        assert set(job.keys()) == {
            'name', 'job_id', 'user_id', 'status_code', 'execution_started', 'request_time', 'priority', 'credit_cost'
        }
        assert job['request_time'] <= dynamo.util.format_time(datetime.now(timezone.utc))
        assert job['user_id'] == 'user1'
        assert job['status_code'] == 'PENDING'
        assert job['execution_started'] is False
        assert job['credit_cost'] == 1

    assert tables.jobs_table.scan()['Items'] == jobs

    assert tables.users_table.scan()['Items'] == [
        {'user_id': 'user1', 'remaining_credits': 7, 'month_of_last_credits_reset': '2024-02'}
    ]


def test_put_jobs_user_exists(tables):
    tables.users_table.put_item(Item={'user_id': 'user1', 'remaining_credits': 5})

    jobs = dynamo.jobs.put_jobs('user1', [{}, {}])

    assert len(jobs) == 2
    assert tables.jobs_table.scan()['Items'] == jobs
    assert tables.users_table.scan()['Items'] == [{'user_id': 'user1', 'remaining_credits': 3}]


def test_put_jobs_insufficient_credits(tables, monkeypatch):
    monkeypatch.setenv('DEFAULT_CREDITS_PER_USER', '1')
    payload = [{'name': 'name1'}, {'name': 'name2'}]

    with unittest.mock.patch('dynamo.user._get_current_month') as mock_get_current_month:
        mock_get_current_month.return_value = '2024-02'
        with pytest.raises(dynamo.jobs.InsufficientCreditsError):
            dynamo.jobs.put_jobs('user1', payload)

    assert tables.jobs_table.scan()['Items'] == []
    assert tables.users_table.scan()['Items'] == [
        {'user_id': 'user1', 'remaining_credits': 1, 'month_of_last_credits_reset': '2024-02'}
    ]


def test_put_jobs_infinite_credits(tables, monkeypatch):
    monkeypatch.setenv('DEFAULT_CREDITS_PER_USER', '1')
    payload = [{'name': 'name1'}, {'name': 'name2'}]

    tables.users_table.put_item(Item={'user_id': 'user1', 'remaining_credits': None})

    jobs = dynamo.jobs.put_jobs('user1', payload)

    assert len(jobs) == 2
    for job in jobs:
        assert job['priority'] == 0


def test_put_jobs_priority_override(tables):
    payload = [{'name': 'name1'}, {'name': 'name2'}]
    tables.users_table.put_item(Item={'user_id': 'user1', 'priority_override': 100, 'remaining_credits': 3})

    jobs = dynamo.jobs.put_jobs('user1', payload)

    assert len(jobs) == 2
    for job in jobs:
        assert job['priority'] == 100

    tables.users_table.put_item(Item={'user_id': 'user1', 'priority_override': 550, 'remaining_credits': None})

    jobs = dynamo.jobs.put_jobs('user1', payload)

    assert len(jobs) == 2
    for job in jobs:
        assert job['priority'] == 550


def test_put_jobs_priority(tables):
    tables.users_table.put_item(Item={'user_id': 'user1', 'remaining_credits': 7})

    jobs = dynamo.jobs.put_jobs(user_id='user1', jobs=[{}, {}, {}])
    assert jobs[0]['priority'] == 7
    assert jobs[1]['priority'] == 6
    assert jobs[2]['priority'] == 5

    jobs.extend(dynamo.jobs.put_jobs(user_id='user1', jobs=[{}, {}, {}, {}]))
    assert jobs[3]['priority'] == 4
    assert jobs[4]['priority'] == 3
    assert jobs[5]['priority'] == 2
    assert jobs[6]['priority'] == 1


def test_put_jobs_priority_extra_credits(tables):
    tables.users_table.put_item(Item={'user_id': 'user1', 'remaining_credits': 10_003})

    jobs = dynamo.jobs.put_jobs(user_id='user1', jobs=[{}])
    assert jobs[0]['priority'] == 9999

    jobs.extend(dynamo.jobs.put_jobs(user_id='user1', jobs=[{}]))
    assert jobs[1]['priority'] == 9999

    jobs.extend(dynamo.jobs.put_jobs(user_id='user1', jobs=[{}] * 6))
    assert jobs[2]['priority'] == 9999
    assert jobs[3]['priority'] == 9999
    assert jobs[4]['priority'] == 9999
    assert jobs[5]['priority'] == 9998
    assert jobs[6]['priority'] == 9997
    assert jobs[7]['priority'] == 9996


def test_put_jobs_decrement_credits_failure(tables):
    with unittest.mock.patch('dynamo.user.decrement_credits') as mock_decrement_credits:
        mock_decrement_credits.side_effect = Exception('test error')
        with pytest.raises(Exception, match=r'^test error$'):
            dynamo.jobs.put_jobs('foo', [{'name': 'job1'}])

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


def test_get_jobs_waiting_for_execution(tables):
    items = [
        {
            'job_id': 'job0',
            'status_code': 'PENDING',
            'execution_started': False
        },
        {
            'job_id': 'job1',
            'status_code': 'PENDING'
        },
        {
            'job_id': 'job2',
            'status_code': 'RUNNING',
            'execution_started': True
        },
        {
            'job_id': 'job3',
            'status_code': 'PENDING',
            'execution_started': True
        },
        {
            'job_id': 'job4',
            'status_code': 'PENDING',
            'execution_started': False
        },
        {
            'job_id': 'job5',
            'status_code': 'PENDING',
            'execution_started': True
        },
        {
            'job_id': 'job6',
            'status_code': 'PENDING',
            'execution_started': False
        },
        {
            'job_id': 'job7',
            'status_code': 'PENDING',
            'execution_started': True
        },
        {
            'job_id': 'job8',
            'status_code': 'RUNNING'
        },
        {
            'job_id': 'job9',
            'status_code': 'PENDING'
        },
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
