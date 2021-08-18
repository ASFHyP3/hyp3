from unittest.mock import patch

import asf_search
import pytest

import process_new_granules


def test_get_neighbors():
    granule = asf_search.ASFProduct({'properties': {'sceneName': 'granule'}, 'geometry': {}}),

    def mock(payload):
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

    with patch('asf_search.baseline_search.stack_from_product', mock):
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
                'job_type': 'INSAR_GAMMA',
                'name': 'SubscriptionName',
                'job_parameters': {
                    'granules': ['GranuleName', 'granule2'],
                }
            },
            {
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
