from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import asf_search
import pytest

import subscription_worker


def test_get_unprocessed_granules(tables):
    items = [
        {
            'job_id': 'job1',
            'request_time': '2021-01-01T00:00:00+00:00',
            'user_id': 'my_user',
            'job_type': 'INSAR_GAMMA',
            'name': 'my_name',
            'job_parameters': {
                'granules': ['processed', 'not_processed'],
            },
        },
        {
            'job_id': 'job2',
            'request_time': '2021-01-01T00:00:00+00:00',
            'user_id': 'different_user',
            'job_type': 'INSAR_GAMMA',
            'name': 'subscription1',
            'job_parameters': {
                'granules': ['not_processed', 'not_processed'],
            },
        },
        {
            'job_id': 'job3',
            'request_time': '2021-01-01T00:00:00+00:00',
            'user_id': 'user1',
            'job_type': 'INSAR_GAMMA',
            'name': 'different_name',
            'job_parameters': {
                'granules': ['not_processed', 'not_processed'],
            },
        },
        {
            'job_id': 'job4',
            'request_time': '2021-01-01T00:00:00+00:00',
            'user_id': 'my_user',
            'job_type': 'RTC_GAMMA',
            'name': 'my_name',
            'job_parameters': {
                'granules': ['not_processed'],
            },
        },
    ]
    for item in items:
        tables.jobs_table.put_item(Item=item)

    subscription = {
        'user_id': 'my_user',
        'job_specification': {
            'job_type': 'INSAR_GAMMA',
            'name': 'my_name',
        },
        'search_parameters': {
            'foo': 'bar',
        },
    }

    search_results = [
        asf_search.ASFProduct({'properties': {'sceneName': 'processed'}, 'geometry': {}, 'baseline': 1}),
        asf_search.ASFProduct({'properties': {'sceneName': 'not_processed'}, 'geometry': {}, 'baseline': 1}),
    ]

    def mock_search(**kwargs):
        assert kwargs == subscription['search_parameters']
        return asf_search.ASFSearchResults(search_results)

    with patch('asf_search.search', mock_search):
        results = subscription_worker.get_unprocessed_granules(subscription)
        assert results == search_results[1:]


def test_get_neighbors():
    granule = asf_search.ASFProduct({'properties': {'sceneName': 'granule'}, 'geometry': {}, 'baseline': 1}),

    def mock_stack_from_product(payload):
        assert payload == granule
        return asf_search.ASFSearchResults([
            asf_search.ASFProduct(
                {'properties': {'sceneName': 'S1A_A', 'temporalBaseline': -3}, 'geometry': {}, 'baseline': 1}),
            asf_search.ASFProduct(
                {'properties': {'sceneName': 'S1B_B', 'temporalBaseline': -2}, 'geometry': {}, 'baseline': 1}),
            asf_search.ASFProduct(
                {'properties': {'sceneName': 'S1A_C', 'temporalBaseline': -1}, 'geometry': {}, 'baseline': 1}),
            asf_search.ASFProduct(
                {'properties': {'sceneName': 'S1B_D', 'temporalBaseline': 0}, 'geometry': {}, 'baseline': 1}),
            asf_search.ASFProduct(
                {'properties': {'sceneName': 'S1A_E', 'temporalBaseline': 1}, 'geometry': {}, 'baseline': 1}),
            asf_search.ASFProduct(
                {'properties': {'sceneName': 'S1B_F', 'temporalBaseline': 2}, 'geometry': {}, 'baseline': 1}),
            asf_search.ASFProduct(
                {'properties': {'sceneName': 'S1A_G', 'temporalBaseline': 3}, 'geometry': {}, 'baseline': 1}),
        ])

    with patch('asf_search.baseline_search.stack_from_product', mock_stack_from_product):
        neighbors = subscription_worker.get_neighbors(granule, 1, 'S1')
        assert neighbors == ['S1A_C']

        neighbors = subscription_worker.get_neighbors(granule, 2, 'S1')
        assert neighbors == ['S1B_B', 'S1A_C']

        neighbors = subscription_worker.get_neighbors(granule, 2, 'S1A')
        assert neighbors == ['S1A_A', 'S1A_C']

        neighbors = subscription_worker.get_neighbors(granule, 5, 'S1B')
        assert neighbors == ['S1B_B']


def test_get_jobs_for_granule():
    granule = asf_search.ASFProduct({'properties': {'sceneName': 'GranuleName'}, 'geometry': {}, 'baseline': 1})
    granule2 = asf_search.ASFProduct({'properties': {'sceneName': 'GranuleName2'}, 'geometry': {}, 'baseline': 1})

    subscription = {
        'subscription_id': 'f00b731f-121d-44dc-abfa-c24afd8ad542',
        'user_id': 'subscriptionsUser',
        'search_parameters': {
            'start': '2020-01-01T00:00:00+00:00',
            'end': '2020-01-01T00:00:00+00:00',
        },
        'job_specification': {
            'job_type': 'RTC_GAMMA',
            'name': 'SubscriptionName',
            'job_parameters': {
                'speckle_filter': True,
            }
        }
    }
    payload = subscription_worker.get_jobs_for_granule(subscription, granule)
    payload2 = subscription_worker.get_jobs_for_granule(subscription, granule2)
    assert payload == [
        {
            'subscription_id': 'f00b731f-121d-44dc-abfa-c24afd8ad542',
            'job_type': 'RTC_GAMMA',
            'name': 'SubscriptionName',
            'job_parameters': {
                'granules': ['GranuleName'],
                'speckle_filter': True,
            },
        }
    ]
    assert payload2 == [
        {
            'subscription_id': 'f00b731f-121d-44dc-abfa-c24afd8ad542',
            'job_type': 'RTC_GAMMA',
            'name': 'SubscriptionName',
            'job_parameters': {
                'granules': ['GranuleName2'],
                'speckle_filter': True,
            },
        }
    ]

    subscription = {
        'subscription_id': '51b576b0-a89b-4108-a9d8-7ecb52aee950',
        'user_id': 'subscriptionsUser',
        'search_parameters': {
            'start': '2020-01-01T00:00:00+00:00',
            'end': '2020-01-01T00:00:00+00:00',
            'platform': 'foo',
        },
        'job_specification': {
            'job_type': 'INSAR_GAMMA',
            'name': 'SubscriptionName'
        }
    }
    mock_granules = ['granule2', 'granule3']
    with patch('subscription_worker.get_neighbors', lambda x, y, z: mock_granules):
        payload = subscription_worker.get_jobs_for_granule(subscription, granule)
        assert payload == [
            {
                'subscription_id': '51b576b0-a89b-4108-a9d8-7ecb52aee950',
                'job_type': 'INSAR_GAMMA',
                'name': 'SubscriptionName',
                'job_parameters': {
                    'granules': ['GranuleName', 'granule2'],
                }
            },
            {
                'subscription_id': '51b576b0-a89b-4108-a9d8-7ecb52aee950',
                'job_type': 'INSAR_GAMMA',
                'name': 'SubscriptionName',
                'job_parameters': {
                    'granules': ['GranuleName', 'granule3'],
                },
            }
        ]

    subscription = {
        'subscription_id': '51b576b0-a89b-4108-a9d8-7ecb52aee950',
        'job_specification': {
            'job_type': 'FOO',
        }
    }
    with pytest.raises(ValueError):
        subscription_worker.get_jobs_for_granule(subscription, granule)


def test_get_jobs_for_subscription():
    def mock_get_unprocessed_granules(subscription):
        assert subscription == {}
        return ['a', 'b', 'c']

    def mock_get_jobs_for_granule(subscription, granule):
        return [{'granule': granule}]

    with patch('subscription_worker.get_unprocessed_granules', mock_get_unprocessed_granules):
        with patch('subscription_worker.get_jobs_for_granule', mock_get_jobs_for_granule):

            result = subscription_worker.get_jobs_for_subscription(subscription={}, limit=20)
            assert result == [
                {'granule': 'a'},
                {'granule': 'b'},
                {'granule': 'c'},
            ]

            result = subscription_worker.get_jobs_for_subscription(subscription={}, limit=1)
            assert result == [
                {'granule': 'a'},
            ]

            result = subscription_worker.get_jobs_for_subscription(subscription={}, limit=0)
            assert result == []


def test_lambda_handler(tables):
    items = [
        {
            'subscription_id': 'sub1',
            'creation_date': '2020-01-01T00:00:00+00:00',
            'job_type': 'INSAR_GAMMA',
            'search_parameters': {
                'start': datetime.now(tz=timezone.utc).isoformat(timespec='seconds'),
                'end': (datetime.now(tz=timezone.utc) + timedelta(days=5)).isoformat(timespec='seconds'),
            },
            'user_id': 'user1',
            'enabled': True,
        },
        {
            'subscription_id': 'sub2',
            'creation_date': '2020-01-01T00:00:00+00:00',
            'job_type': 'INSAR_GAMMA',
            'user_id': 'user1',
            'enabled': False
        },
        {
            'subscription_id': 'sub3',
            'creation_date': '2020-01-01T00:00:00+00:00',
            'job_type': 'INSAR_GAMMA',
            'search_parameters': {
                'start': (datetime.now(tz=timezone.utc) - timedelta(days=15)).isoformat(timespec='seconds'),
                'end': (datetime.now(tz=timezone.utc) - timedelta(days=5)).isoformat(timespec='seconds'),
            },
            'user_id': 'user1',
            'enabled': True,
        },
        {
            'subscription_id': 'sub4',
            'creation_date': '2020-01-01T00:00:00+00:00',
            'job_type': 'INSAR_GAMMA',
            'search_parameters': {
                'start': (datetime.now(tz=timezone.utc) - timedelta(days=15)).isoformat(timespec='seconds'),
                'end': (datetime.now(tz=timezone.utc) - timedelta(days=5)).isoformat(timespec='seconds'),
            },
            'user_id': 'user1',
            'enabled': True,
        },
    ]
    for item in items:
        tables.subscriptions_table.put_item(Item=item)

    def mock_get_unprocessed_granules(subscription):
        if subscription['subscription_id'] == 'sub4':
            return ['notempty']
        else:
            return []

    with patch('subscription_worker.handle_subscription') as mock_handle_subscription:
        with patch('subscription_worker.get_unprocessed_granules', mock_get_unprocessed_granules):
            subscription_worker.lambda_handler({'subscription': items[0]}, None)

            with pytest.raises(ValueError, match=r'subscription sub2 is disabled'):
                subscription_worker.lambda_handler({'subscription': items[1]}, None)

            subscription_worker.lambda_handler({'subscription': items[2]}, None)
            subscription_worker.lambda_handler({'subscription': items[3]}, None)

        assert mock_handle_subscription.call_count == 3

    response = tables.subscriptions_table.scan()['Items']

    sub1 = [sub for sub in response if sub['subscription_id'] == 'sub1'][0]
    assert sub1['enabled'] is True

    sub3 = [sub for sub in response if sub['subscription_id'] == 'sub3'][0]
    assert sub3['enabled'] is False

    sub4 = [sub for sub in response if sub['subscription_id'] == 'sub4'][0]
    assert sub4['enabled'] is True
