import pytest

from hyp3_api import auth


@pytest.mark.network
def test_get_jwks_client(client):
    assert 'urs.earthdata.nasa.gov' in client.uri


@pytest.mark.network
def test_bad_bearer_token(client):
    with pytest.raises(auth.InvalidTokenException, match=r'.*Invalid authorization token provided.*'):
        auth.decode_edl_bearer_token('bad token', client)


def test_bad_asf_cookie(client, monkeypatch):
    monkeypatch.setenv("AUTH_PUBLIC_KEY", "public key")
    monkeypatch.setenv("AUTH_ALGORITHM", "RS256")

    with pytest.raises(auth.InvalidTokenException, match=r'.*Invalid authorization cookie provided.*'):
        auth.decode_asf_cookie('bad token')


@pytest.fixture(scope='session')
def client():
    return auth.get_jwks_client()
