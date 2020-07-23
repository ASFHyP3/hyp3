from conftest import AUTH_COOKIE, JOBS_URI, USER_URI, login, make_job, submit_batch
from flask_api import status

from hyp3_api import auth


ENDPOINTS = {
    JOBS_URI: {'GET', 'HEAD', 'OPTIONS', 'POST'},
    USER_URI: {'GET', 'HEAD', 'OPTIONS'},
}


def test_options(client):
    all_methods = {'GET', 'HEAD', 'OPTIONS', 'POST', 'PUT', 'DELETE'}

    login(client)
    for uri, good_methods in ENDPOINTS.items():
        response = client.options(uri)
        assert response.status_code == status.HTTP_200_OK
        allowed_methods = response.headers['allow'].split(', ')
        assert set(allowed_methods) == good_methods

        for bad_method in all_methods - good_methods:
            response = client.open(uri, method=bad_method)
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_not_logged_in(client):
    for uri, methods in ENDPOINTS.items():
        for method in methods:
            response = client.open(uri, method=method)
            if method == 'OPTIONS':
                assert response.status_code == status.HTTP_200_OK
            else:
                assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_invalid_cookie(client):
    for uri in ENDPOINTS:
        client.set_cookie('localhost', AUTH_COOKIE, 'garbage I say!!! GARGBAGE!!!')
        response = client.get(uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_expired_cookie(client):
    for uri in ENDPOINTS:
        client.set_cookie('localhost', AUTH_COOKIE, auth.get_mock_jwt_cookie('user', -1))
        response = client.get(uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_good_granule_names(client, table):
    login(client)
    good_granule_names = [
        'S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38',
        'S1A_IW_SLC__1SSH_20150608T205059_20150608T205126_006287_0083E8_C4F0',
    ]
    for granule in good_granule_names:
        batch = [
            make_job(granule)
        ]
        response = submit_batch(client, batch)
        assert response.status_code == status.HTTP_200_OK


def test_bad_granule_names(client):
    login(client)
    bad_granule_names = [
        'foo',
        'S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E3',
        'S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38_',
    ]
    for granule in bad_granule_names:
        batch = [
            make_job(granule)
        ]
        response = submit_batch(client, batch)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_bad_beam_modes(client):
    login(client)
    bad_beam_modes = [
        'S1B_S3_SLC__1SDV_20200604T091417_20200604T091430_021882_029879_5765',
        'S1B_WV_SLC__1SSV_20200519T140110_20200519T140719_021651_0291AA_2A86',
        'S1B_EW_SLC__1SDH_20200605T065551_20200605T065654_021895_0298DC_EFB5',
    ]
    for granule in bad_beam_modes:
        batch = [
            make_job(granule)
        ]
        response = submit_batch(client, batch)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_bad_product_types(client):
    login(client)
    bad_product_types = [
        'S1A_IW_GRDH_1SDV_20200604T190627_20200604T190652_032871_03CEB7_56F3',
        'S1B_IW_OCN__2SDV_20200518T220815_20200518T220851_021642_02915F_B404',
        'S1B_IW_RAW__0SDV_20200605T145138_20200605T145210_021900_029903_AFF4',
    ]
    for granule in bad_product_types:
        batch = [
            make_job(granule)
        ]
        response = submit_batch(client, batch)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_no_route(client):
    response = client.get('/no/such/path')
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_cors_no_origin(client):
    for uri in ENDPOINTS:
        response = client.get(uri)
        assert 'Access-Control-Allow-Origin' not in response.headers
        assert 'Access-Control-Allow-Credentials' not in response.headers


def test_cors_bad_origins(client):
    bad_origins = [
        'https://www.google.com',
        'https://www.alaska.edu',
    ]
    for uri in ENDPOINTS:
        for origin in bad_origins:
            response = client.get(uri, headers={'Origin': origin})
            assert 'Access-Control-Allow-Origin' not in response.headers
            assert 'Access-Control-Allow-Credentials' not in response.headers


def test_cors_good_origins(client):
    good_origins = [
        'https://search.asf.alaska.edu',
        'https://search-test.asf.alaska.edu',
        'http://local.asf.alaska.edu',
    ]
    for uri in ENDPOINTS:
        for origin in good_origins:
            response = client.get(uri, headers={'Origin': origin})
            assert response.headers['Access-Control-Allow-Origin'] == origin
            assert response.headers['Access-Control-Allow-Credentials'] == 'true'
