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

    payload = process_new_granules.get_payload_for_job(subscription, granule)
    assert payload == {
        'job_type': 'RTC_GAMMA',
        'name': 'SubscriptionName',
        'job_parameters': {
            'granules': ['GranuleName'],
        },
    }


def test_submit_jobs_for_granule(tables):
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
    granule = 'granule1'

    process_new_granules.submit_jobs_for_granule(subscription, granule)

    response = tables.jobs_table.scan()['Items']
    assert 'job_id' in response[0]
    del response[0]['job_id']
    assert 'request_time' in response[0]
    assert isinstance(response[0]['request_time'], str)
    del response[0]['request_time']
    assert response == [
        {
            'job_type': 'RTC_GAMMA',
            'name': 'SubscriptionName',
            'user_id': 'subscriptionsUser',
            'status_code': 'PENDING',
            'job_parameters': {
                'granules': ['granule1'],
            }
        }
    ]
