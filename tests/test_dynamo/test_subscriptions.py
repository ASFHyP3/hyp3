from datetime import datetime, timedelta, timezone

import pytest

import dynamo


def test_put_subscription(tables):
    subscription = {
        'job_definition': {
            'job_type': 'RTC_GAMMA',
            'name': 'sub1',
        },
        'search_parameters': {
            'start': '2020-01-01T00:00:00+00:00',
            'end': '2020-01-02T00:00:00+00:00',
        }
    }
    response = dynamo.subscriptions.put_subscription('user1', subscription)
    assert [response] == tables.subscriptions_table.scan()['Items']

    assert 'subscription_id' in response
    assert isinstance(response['subscription_id'], str)
    del response['subscription_id']

    assert response == {
        'user_id': 'user1',
        'job_definition': {
            'job_type': 'RTC_GAMMA',
            'name': 'sub1',
        },
        'search_parameters': {
            'start': '2020-01-01T00:00:00+00:00',
            'end': '2020-01-02T00:00:00+00:00',
            'beamMode': ['IW'],
            'platform': 'S1',
            'polarization': ['VV', 'VV+VH', 'HH', 'HH+HV'],
            'processingLevel': 'SLC',
        }
    }


def test_validate_subscription():
    subscription = {
        'search_parameters': {
            'start': '2021-01-01T00:00:00+00:00',
        }
    }

    good_end_dates = [
        '2021-01-01T00:00:00-00:01',
        '2021-01-01T00:01:00+00:00',
        dynamo.util.format_time(datetime.now(tz=timezone.utc) + timedelta(days=180)),
    ]

    bad_end_dates = [
        '2021-01-01T00:00:00+00:00',
        '2021-01-01T00:00:00+00:01',
        dynamo.util.format_time(datetime.now(tz=timezone.utc) + timedelta(days=180, seconds=1)),
    ]

    for end in bad_end_dates:
        subscription['search_parameters']['end'] = end
        with pytest.raises(ValueError):
            dynamo.subscriptions.validate_subscription(subscription)

    for end in good_end_dates:
        subscription['search_parameters']['end'] = end
        dynamo.subscriptions.validate_subscription(subscription)


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


def test_get_all_subscriptions(tables):
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
