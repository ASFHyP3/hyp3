import pytest

from hyp3_api import auth
from test_api import conftest


def test_decode_asf_cookie(monkeypatch, jwks_client):
    cookie = conftest.get_mock_jwt_cookie('user', lifetime_in_seconds=100, access_token='token')

    user, token = auth.decode_asf_cookie(cookie)
    assert user == 'user'
    assert token == 'token'


@pytest.mark.network
def test_decode_edl_bearer_token(monkeypatch, jwks_client):
    def mock_decode(*args, **kwargs):
        return {'uid': 'test-user'}

    monkeypatch.setattr(auth.jwt, 'decode', mock_decode)

    user, token = auth.decode_edl_bearer_token('test-token', jwks_client)
    assert user == 'test-user'
    assert token == 'test-token'


@pytest.mark.network
def test_get_jwks_client(jwks_client):
    assert 'urs.earthdata.nasa.gov' in jwks_client.uri


@pytest.mark.network
def test_bad_bearer_token(jwks_client):
    with pytest.raises(auth.InvalidTokenException, match=r'.*Invalid authorization token provided.*'):
        auth.decode_edl_bearer_token('bad token', jwks_client)


def test_bad_asf_cookie(jwks_client, monkeypatch):
    with pytest.raises(auth.InvalidTokenException, match=r'.*Invalid authorization cookie provided.*'):
        auth.decode_asf_cookie('bad token')


@pytest.fixture(scope='session')
def jwks_client():
    return auth.get_jwks_client()
