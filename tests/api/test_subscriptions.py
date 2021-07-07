from conftest import SUBSCRIPTIONS_URI, login


def test_post_subscription(client):
    login(client)
    params = {
        'search_parameters': {
            'foo': 'bar',
        },
        'job_parameters': {
            'granules': ['S1A_IW_SLC__1SDV_20200720T172109_20200720T172128_033541_03E2FB_341F',
                         'S1A_IW_SLC__1SDV_20200813T172110_20200813T172129_033891_03EE3F_2C3E', ],
            'looks': '10x2',
            'include_inc_map': True,
            'include_look_vectors': True,
            'include_los_displacement': True,
            'include_dem': True,
            'include_wrapped_phase': True,
        },
        'job_type': 'INSAR_GAMMA',
        'name': 'SubscriptionName'
    }

    response = client.post(SUBSCRIPTIONS_URI, json=params)

    assert response.json == params
