from http import HTTPStatus

from test_api.conftest import AUTH_COOKIE, JOBS_URI, SUBSCRIPTIONS_URI, USER_URI, login

from hyp3_api import auth, routes

ENDPOINTS = {
    JOBS_URI: {'GET', 'HEAD', 'OPTIONS', 'POST'},
    JOBS_URI + '/foo': {'GET', 'HEAD', 'OPTIONS'},
    USER_URI: {'GET', 'HEAD', 'OPTIONS'},
    SUBSCRIPTIONS_URI: {'GET', 'HEAD', 'OPTIONS', 'POST'},
    SUBSCRIPTIONS_URI + '/foo': {'GET', 'HEAD', 'OPTIONS', 'PATCH'},
}


def test_options(client):
    all_methods = {'GET', 'HEAD', 'OPTIONS', 'POST', 'PUT', 'DELETE', 'PATCH'}

    login(client)
    for uri, good_methods in ENDPOINTS.items():
        response = client.options(uri)
        assert response.status_code == HTTPStatus.OK
        allowed_methods = response.headers['allow'].split(', ')
        assert set(allowed_methods) == good_methods

        for bad_method in all_methods - good_methods:
            response = client.open(uri, method=bad_method)
            assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_not_logged_in(client):
    for uri, methods in ENDPOINTS.items():
        for method in methods:
            response = client.open(uri, method=method)
            if method == 'OPTIONS':
                assert response.status_code == HTTPStatus.OK
            else:
                assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_invalid_cookie(client):
    for uri in ENDPOINTS:
        client.set_cookie('localhost', AUTH_COOKIE, 'garbage I say!!! GARGBAGE!!!')
        response = client.get(uri)
        assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_expired_cookie(client):
    for uri in ENDPOINTS:
        client.set_cookie('localhost', AUTH_COOKIE, auth.get_mock_jwt_cookie('user', -1))
        response = client.get(uri)
        assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_no_route(client):
    response = client.get('/no/such/path')
    assert response.status_code == HTTPStatus.NOT_FOUND


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


def test_hyp3_unavailable(client, monkeypatch):
    monkeypatch.setenv('SYSTEM_AVAILABLE', 'false')
    for uri, methods in ENDPOINTS.items():
        for method in methods:
            response = client.open(uri, method=method)
            assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_redirect_root(client):
    response = client.get('/')
    assert response.location.endswith('/ui/')
    assert response.status_code == HTTPStatus.FOUND


def test_ui_location(client):
    response = client.get('/ui')
    assert response.status_code == HTTPStatus.PERMANENT_REDIRECT
    assert response.location.endswith('/ui/')

    response = client.get('/ui/')
    assert response.status_code == HTTPStatus.OK


def test_wkt_validator(client):
    validator = routes.WKTValidator()

    assert not validator.validate('foo')
    assert validator.validate('POLYGON((-5 2, -3 2, -3 5, -5 5, -5 2))')


def test_banned_ip_address(client):
    good_addresses = ['2.2.2.1', '2.2.2.3', '1.1.2.1']
    for good_address in good_addresses:
        client.environ_base = {'REMOTE_ADDR': good_address}
        response = client.get('/ui/')
        assert response.status_code == HTTPStatus.OK

    bad_addresses = ['1.1.1.1', '1.1.1.255', '2.2.2.2']
    for bad_address in bad_addresses:
        client.environ_base = {'REMOTE_ADDR': bad_address}
        response = client.get('/ui/')
        assert response.status_code == HTTPStatus.FORBIDDEN
