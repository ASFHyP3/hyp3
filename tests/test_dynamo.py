from decimal import Decimal

from api.conftest import list_have_same_elements

import dynamo
from hyp3_api.util import convert_floats_to_decimals


def test_count_jobs(tables):
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

    assert dynamo.jobs.count_jobs('user1') == 2
    assert dynamo.jobs.count_jobs('user2') == 1


def test_count_jobs_by_start(tables):
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

    start = '2000-01-01T00:00:00+00:00'
    end = '2000-01-03T00:00:00+00:00'
    response = dynamo.jobs.count_jobs('user1', start, end)
    assert response == 3

    start = '2000-01-01T00:00:01+00:00'
    end = '2000-01-02T00:59:59+00:00'
    response = dynamo.jobs.count_jobs('user1', start, end)
    assert response == 1

    start = '2000-01-01T00:00:01+00:00'
    response = dynamo.jobs.count_jobs('user1', start, None)
    assert response == 2

    end = '2000-01-02T00:59:59+00:00'
    response = dynamo.jobs.count_jobs('user1', None, end)
    assert response == 2


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


def test_put_jobs(tables):
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
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
        {
            'job_id': 'job3',
            'name': 'name2',
            'user_id': 'user2',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
    ]
    dynamo.jobs.put_jobs(table_items)
    response = tables.jobs_table.scan()
    assert response['Items'] == table_items


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


def test_get_user(tables):
    table_items = [
        {
            'user_id': 'user1',
            'max_jobs_per_user': 5
        },
        {
            'user_id': 'user2',
            'max_jobs_per_user': 15
        },
    ]
    for item in table_items:
        tables.users_table.put_item(Item=item)

    assert dynamo.user.get_user('user1') == table_items[0]
    assert dynamo.user.get_user('user2') == table_items[1]
    assert dynamo.user.get_user('foo') is None


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

    dynamo.jobs.update_job('job1', {'status_code': 'status2'})

    response = tables.jobs_table.scan()
    expected_response = [
        {
            'job_id': 'job1',
            'name': 'name1',
            'user_id': 'user1',
            'status_code': 'status2',
            'request_time': '2000-01-01T00:00:00+00:00',
        },
    ]
    assert response['Items'] == expected_response


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
        tables.jobs_table.put_item(Item=convert_floats_to_decimals(item))

    response, _ = dynamo.jobs.query_jobs('user1')
    assert response[0]['float_value'] == Decimal('30.04')
    assert response[1]['float_value'] == Decimal('0.0')
    assert response[2]['float_value'] == Decimal('0.1')


def test_put_subscription(tables):
    table_items = [
        {
            'subscription_id': 'sub1',
            'job_type': 'INSAR_GAMMA',
            'user_id': 'user1'
        },
    ]
    dynamo.subscriptions.put_subscription(table_items[0])
    response = tables.subscriptions_table.scan()
    assert response['Items'] == table_items


def test_get_subscriptions_for_user(tables):
    table_items = [
        {
            'subscription_id': 'sub1',
            'job_type': 'INSAR_GAMMA',
            'user_id': 'user1'
        },
        {
            'subscription_id': 'sub2',
            'job_type': 'INSAR_GAMMA',
            'user_id': 'user1'
        },
        {
            'subscription_id': 'sub3',
            'job_type': 'INSAR_GAMMA',
            'user_id': 'user1'
        },
        {
            'subscription_id': 'sub4',
            'job_type': 'INSAR_GAMMA',
            'user_id': 'user2'
        },
    ]
    for item in table_items:
        tables.subscriptions_table.put_item(Item=item)
    response = dynamo.subscriptions.get_subscriptions_for_user('user1')
    assert response == table_items[:3]
    response = dynamo.subscriptions.get_subscriptions_for_user('user2')
    assert response == [table_items[3]]


def test_get_subscriptions_for_user(tables):
    table_items = [
        {
            'subscription_id': 'sub1',
            'job_type': 'INSAR_GAMMA',
            'user_id': 'user1'
        },
        {
            'subscription_id': 'sub2',
            'job_type': 'INSAR_GAMMA',
            'user_id': 'user1'
        },
        {
            'subscription_id': 'sub3',
            'job_type': 'INSAR_GAMMA',
            'user_id': 'user1'
        },
        {
            'subscription_id': 'sub4',
            'job_type': 'INSAR_GAMMA',
            'user_id': 'user2'
        },
    ]
    for item in table_items:
        tables.subscriptions_table.put_item(Item=item)
    response = dynamo.subscriptions.get_all_subscriptions()
    assert response == table_items
