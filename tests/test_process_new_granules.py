from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import asf_search
import pytest

import process_new_granules


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
        asf_search.ASFProduct({'properties': {'sceneName': 'processed'}, 'geometry': {}}),
        asf_search.ASFProduct({'properties': {'sceneName': 'not_processed'}, 'geometry': {}}),
    ]

    def mock_search(**kwargs):
        assert kwargs == subscription['search_parameters']
        return asf_search.ASFSearchResults(search_results)

    with patch('asf_search.search', mock_search):
        results = process_new_granules.get_unprocessed_granules(subscription)
        assert results == search_results[1:]


def test_get_neighbors():
    granule = asf_search.ASFProduct({'properties': {'sceneName': 'granule'}, 'geometry': {}}),

    def mock_stack_from_product(payload):
        assert payload == granule
        return asf_search.ASFSearchResults([
            asf_search.ASFProduct({'properties': {'sceneName': 'S1A_A', 'temporalBaseline': -3}, 'geometry': {}}),
            asf_search.ASFProduct({'properties': {'sceneName': 'S1B_B', 'temporalBaseline': -2}, 'geometry': {}}),
            asf_search.ASFProduct({'properties': {'sceneName': 'S1A_C', 'temporalBaseline': -1}, 'geometry': {}}),
            asf_search.ASFProduct({'properties': {'sceneName': 'S1B_D', 'temporalBaseline': 0}, 'geometry': {}}),
            asf_search.ASFProduct({'properties': {'sceneName': 'S1A_E', 'temporalBaseline': 1}, 'geometry': {}}),
            asf_search.ASFProduct({'properties': {'sceneName': 'S1B_F', 'temporalBaseline': 2}, 'geometry': {}}),
            asf_search.ASFProduct({'properties': {'sceneName': 'S1A_G', 'temporalBaseline': 3}, 'geometry': {}}),
        ])

    with patch('asf_search.baseline_search.stack_from_product', mock_stack_from_product):
        neighbors = process_new_granules.get_neighbors(granule, 1, 'S1')
        assert neighbors == ['S1A_C']

        neighbors = process_new_granules.get_neighbors(granule, 2, 'S1')
        assert neighbors == ['S1B_B', 'S1A_C']

        neighbors = process_new_granules.get_neighbors(granule, 2, 'S1A')
        assert neighbors == ['S1A_A', 'S1A_C']

        neighbors = process_new_granules.get_neighbors(granule, 5, 'S1B')
        assert neighbors == ['S1B_B']


def test_get_jobs_for_granule():
    granule = asf_search.ASFProduct({'properties': {'sceneName': 'GranuleName'}, 'geometry': {}})

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
    payload = process_new_granules.get_jobs_for_granule(subscription, granule)
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

    subscription = {
        'subscription_id': 'f00b731f-121d-44dc-abfa-c24afd8ad542',
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
    with patch('process_new_granules.get_neighbors', lambda x, y, z: mock_granules):
        payload = process_new_granules.get_jobs_for_granule(subscription, granule)
        assert payload == [
            {
                'subscription_id': 'f00b731f-121d-44dc-abfa-c24afd8ad542',
                'job_type': 'INSAR_GAMMA',
                'name': 'SubscriptionName',
                'job_parameters': {
                    'granules': ['GranuleName', 'granule2'],
                }
            },
            {
                'subscription_id': 'f00b731f-121d-44dc-abfa-c24afd8ad542',
                'job_type': 'INSAR_GAMMA',
                'name': 'SubscriptionName',
                'job_parameters': {
                    'granules': ['GranuleName', 'granule3'],
                },
            }
        ]

    subscription = {
        'job_specification': {
            'job_type': 'FOO',
        }
    }
    with pytest.raises(ValueError):
        process_new_granules.get_jobs_for_granule(subscription, granule)


def test_lambda_handler(tables):
    items = [
        {
            'subscription_id': 'sub1',
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
            'job_type': 'INSAR_GAMMA',
            'user_id': 'user1',
            'enabled': False
        },
        {
            'subscription_id': 'sub3',
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

    with patch('process_new_granules.handle_subscription') as p:
        process_new_granules.lambda_handler(1, 1)
        assert p.call_count == 2

    response = tables.subscriptions_table.scan()['Items']
    sub3 = [sub for sub in response if sub['subscription_id'] == 'sub3'][0]
    assert sub3['enabled'] is False
