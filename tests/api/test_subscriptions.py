from http import HTTPStatus

from conftest import SUBSCRIPTIONS_URI, login


def test_post_subscription(client, tables):
    login(client)
    params = {
        'search_parameters': {
            'start': '2020-01-01T00:00:00+00:00',
            'end': '2020-01-01T00:00:00+00:00',
        },
        'job_specification': {
            'job_parameters': {
                'looks': '10x2',
                'include_inc_map': True,
                'include_look_vectors': True,
                'include_los_displacement': True,
                'include_dem': True,
                'include_wrapped_phase': True,
            },
            'job_type': 'RTC_GAMMA',
            'name': 'SubscriptionName'
        }
    }

    response = client.post(SUBSCRIPTIONS_URI, json=params)
    assert response.status_code == HTTPStatus.OK
    assert 'subscription_id' in response.json
    assert 'user_id' in response.json
    for k, v in params.items():
        assert response.json[k] == v


def test_submit_subscriptions_missing_fields(client, tables):
    login(client)
    params = {}
    response = client.post(SUBSCRIPTIONS_URI, json=params)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    params = {
        'search_parameters': {
            'start': '2020-01-01T00:00:00+00:00',
            'end': '2020-01-01T00:00:00+00:00',
        },
    }
    response = client.post(SUBSCRIPTIONS_URI, json=params)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    params = {
        'search_parameters': {
            'start': '2020-01-01T00:00:00+00:00',
            'end': '2020-01-01T00:00:00+00:00',
        },
        'job_specification': {
            'job_type': 'INSAR_GAMMA',
            'name': 'SubscriptionName'
        }
    }
    response = client.post(SUBSCRIPTIONS_URI, json=params)
    assert response.status_code == HTTPStatus.OK


def test_search_criteria(client, tables):
    login(client)
    params = {
        'search_parameters': {
            'start': '2020-01-01T00:00:00+00:00',
            'end': '2020-01-01T00:00:00+00:00',
            'asfframe': 50,
            'beamMode': 'IW',
            'flightDirection': 'ASCENDING',
            'intersectsWith': 'POLYGON((-5 2, -3 2, -3 5, -5 5, -5 2))',
            'processingLevel': 'GRD_HD',
            'polorization': 'VV',
        },
        'job_specification': {
            'job_type': 'INSAR_GAMMA',
            'name': 'SubscriptionName'
        }
    }
    response = client.post(SUBSCRIPTIONS_URI, json=params)
    assert response.status_code == HTTPStatus.OK

    bad_params = {
        'asfframe': 99999,
        'beamMode': 'EW',
        'flightDirection': 'Foo',
        'intersectsWith': '-190,400,200,90',
        'processingLevel': 'OCN',
        'polorization': 'DUAL VV',
    }
    for k, v in bad_params.items():
        params = {
            'search_parameters': {
                'start': '2020-01-01T00:00:00+00:00',
                'end': '2020-01-01T00:00:00+00:00',
                k: v,
            },
        }
        response = client.post(SUBSCRIPTIONS_URI, json=params)
        assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_subscriptions(client, tables):
    login(client, username='subscriptionsUser')
    response = client.get(SUBSCRIPTIONS_URI)
    assert response.status_code == HTTPStatus.OK
    assert response.json == []

    items = [
        {
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
        },
        {
            'subscription_id': '140191ab-486b-4080-ab1b-3e2c40aab6b8',
            'user_id': 'subscriptionsUser',
            'search_parameters': {
                'start': '2020-01-01T00:00:00+00:00',
                'end': '2020-01-01T00:00:00+00:00',
            },
            'job_specification': {
                'job_type': 'RTC_GAMMA',
                'name': 'SubscriptionName'
            }
        },
        {
            'subscription_id': '92da7534-1896-410a-99e4-d16a20c71861',
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
    ]
    for item in items:
        tables.subscriptions_table.put_item(Item=item)
    response = client.get(SUBSCRIPTIONS_URI)
    assert response.json == items
    assert response.status_code == HTTPStatus.OK
