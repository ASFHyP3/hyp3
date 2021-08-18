from datetime import datetime, timedelta, timezone
from http import HTTPStatus

from unittest.mock import patch
import pytest

from .conftest import SUBSCRIPTIONS_URI, login


def test_post_subscription(client, tables):
    login(client)
    params = {
        'search_parameters': {
            'start': '2020-01-01T00:00:00+00:00',
            'end': '2020-01-02T00:00:00+00:00',
            'platform': 'S1',
            'beamMode': ['IW'],
            'polarization': ['VV'],
            'processingLevel': 'SLC',
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
            'end': '2020-01-02T00:00:00+00:00',
        },
    }
    response = client.post(SUBSCRIPTIONS_URI, json=params)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    params = {
        'search_parameters': {
            'start': '2020-01-01T00:00:00+00:00',
            'end': '2020-01-02T00:00:00+00:00',
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
            'end': '2020-01-02T00:00:00+00:00',
            'frame': [50],
            'relativeOrbit': [1, 5],
            'flightDirection': 'ASCENDING',
            'intersectsWith': 'POLYGON((-5 2, -3 2, -3 5, -5 5, -5 2))',
            'processingLevel': 'GRD_HD',
            'polarization': ['VV'],
        },
        'job_specification': {
            'job_type': 'RTC_GAMMA',
            'name': 'SubscriptionName'
        }
    }
    response = client.post(SUBSCRIPTIONS_URI, json=params)
    assert response.status_code == HTTPStatus.OK

    bad_params = {
        'frame': [99999],
        'relativeOrbit': 123,
        'flightDirection': 'Foo',
        'intersectsWith': '-190,400,200,90',
        'processingLevel': 'OCN',
        'polarization': ['DUAL VV'],
        'undefined': 'foo',
    }
    for k, v in bad_params.items():
        params = {
            'search_parameters': {
                'start': '2020-01-01T00:00:00+00:00',
                'end': '2020-01-02T00:00:00+00:00',
                k: v,
            },
            'job_specification': {
                'job_type': 'RTC_GAMMA',
                'name': 'SubscriptionName'
            }
        }
        response = client.post(SUBSCRIPTIONS_URI, json=params)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    params = {
        'search_parameters': {
            'start': '2020-01-01T00:00:00+00:00',
            'end': '2020-01-01T00:00:00+00:00',
        },
        'job_specification': {
            'job_type': 'RTC_GAMMA',
            'name': 'SubscriptionName'
        }
    }
    response = client.post(SUBSCRIPTIONS_URI, json=params)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_subscriptions(client, tables):
    login(client, username='subscriptionsUser')
    response = client.get(SUBSCRIPTIONS_URI)
    assert response.status_code == HTTPStatus.OK
    assert response.json == {'subscriptions': []}

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
    assert response.json == {'subscriptions': items}
    assert response.status_code == HTTPStatus.OK


def test_update_subscription(client, tables):
    login(client, 'user1')
    subscription = {
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
        },
        'subscription_id': 'a97cefdf-1aa7-4bfd-9785-ff93b3e3d621',
        'job_type': 'INSAR_GAMMA',
        'user_id': 'user1',
    }
    tables.subscriptions_table.put_item(Item=subscription)

    api_response = client.patch(SUBSCRIPTIONS_URI + '/a97cefdf-1aa7-4bfd-9785-ff93b3e3d621',
                                json={'end': '2020-02-02T00:00:00+00:00'})
    assert api_response.status_code == HTTPStatus.OK
    assert api_response.json == {
        'job_definition': {
            'job_type': 'RTC_GAMMA',
            'name': 'sub1',
        },
        'search_parameters': {
            'start': '2020-01-01T00:00:00+00:00',
            'end': '2020-02-02T00:00:00+00:00',

            'beamMode': ['IW'],
            'platform': 'S1',
            'polarization': ['VV', 'VV+VH', 'HH', 'HH+HV'],
            'processingLevel': 'SLC',
        },
        'subscription_id': 'a97cefdf-1aa7-4bfd-9785-ff93b3e3d621',
        'job_type': 'INSAR_GAMMA',
        'user_id': 'user1',
    }

    response = tables.subscriptions_table.scan()

    assert response['Items'][0] == {
        'job_definition': {
            'job_type': 'RTC_GAMMA',
            'name': 'sub1',
        },
        'search_parameters': {
            'start': '2020-01-01T00:00:00+00:00',
            'end': '2020-02-02T00:00:00+00:00',

            'beamMode': ['IW'],
            'platform': 'S1',
            'polarization': ['VV', 'VV+VH', 'HH', 'HH+HV'],
            'processingLevel': 'SLC',
        },
        'subscription_id': 'a97cefdf-1aa7-4bfd-9785-ff93b3e3d621',
        'job_type': 'INSAR_GAMMA',
        'user_id': 'user1',
    }


def test_update_subscription_wrong_user(client, tables):
    login(client, 'user1')

    subscription = {
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
        },
        'subscription_id': 'a97cefdf-1aa7-4bfd-9785-ff93b3e3d621',
        'job_type': 'INSAR_GAMMA',
        'user_id': 'user2',
    }
    tables.subscriptions_table.put_item(Item=subscription)
    api_response = client.patch(SUBSCRIPTIONS_URI + '/a97cefdf-1aa7-4bfd-9785-ff93b3e3d621',
                                json={'end': '2020-02-02T00:00:00+00:00'})
    assert api_response.status_code == HTTPStatus.FORBIDDEN


def test_update_subscription_date_too_far_out(client, tables):
    login(client, 'user1')

    subscription = {
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
        },
        'subscription_id': 'a97cefdf-1aa7-4bfd-9785-ff93b3e3d621',
        'job_type': 'INSAR_GAMMA',
        'user_id': 'user1',
    }
    tables.subscriptions_table.put_item(Item=subscription)

    end = datetime.now(tz=timezone.utc) + timedelta(days=181)
    api_response = client.patch(SUBSCRIPTIONS_URI + '/a97cefdf-1aa7-4bfd-9785-ff93b3e3d621',
                                json={'end': end})
    assert api_response.status_code == HTTPStatus.BAD_REQUEST
    assert f'End date: {end.isoformat(timespec="seconds")} must be within 180 days' in api_response.json['detail']
