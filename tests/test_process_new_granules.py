import process_new_granuels


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

    process_new_granuels.submit_jobs_for_granule(subscription, granule)

    response = tables.jobs_table.scan()['Items']
    assert 'job_id' in response[0]
    del response[0]['job_id']
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
