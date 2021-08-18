from unittest.mock import patch

import process_new_granules


def test_get_payload_for_job():
    subscription = {
        'subscription_id': 'f00b731f-121d-44dc-abfa-c24afd8ad542',
        'user_id': 'subscriptionsUser',
        'search_parameters': {
            'start': '2020-01-01T00:00:00+00:00',
            'end': '2020-01-01T00:00:00+00:00',
        },
        'job_specification': {
            'job_type': 'RTC_GAMMA',
            'name': 'SubscriptionName'
        }
    }
    granule = 'GranuleName'

    payload = process_new_granules.get_jobs_for_granule(subscription, granule)
    assert payload == [
        {
            'job_type': 'RTC_GAMMA',
            'name': 'SubscriptionName',
            'job_parameters': {
                'granules': ['GranuleName'],
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
    granule = 'granule1'

    mock_granules = ['granule2', 'granule3']
    with patch('process_new_granules.get_neighbors', lambda x, y, z: mock_granules):
        payload = process_new_granules.get_jobs_for_granule(subscription, granule)
        assert payload == [
            {
                'job_type': 'INSAR_GAMMA',
                'name': 'SubscriptionName',
                'job_parameters': {
                    'granules': ['granule1', 'granule2'],
                }
            },
            {
                'job_type': 'INSAR_GAMMA',
                'name': 'SubscriptionName',
                'job_parameters': {
                    'granules': ['granule1', 'granule3'],
                },
            }
        ]
