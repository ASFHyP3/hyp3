from unittest.mock import patch

import jwt
import pytest

from hyp3_api import auth
from test_api import conftest


def test_decode_asf_cookie():
    cookie = conftest.get_mock_jwt_cookie('user', lifetime_in_seconds=100, access_token='token')

    user, token = auth.decode_asf_cookie(cookie)
    assert user == 'user'
    assert token == 'token'


@pytest.mark.network
def test_decode_edl_bearer_token(jwks_client):
    with patch('hyp3_api.auth.jwt.decode', return_value={'uid': 'test-user'}) as mock_decode:
        user, token = auth.decode_edl_bearer_token('test-token', jwks_client)

        mock_decode.assert_called_once()
        assert len(mock_decode.call_args.args) == 2
        assert mock_decode.call_args.args[0] == 'test-token'
        assert isinstance(mock_decode.call_args.args[1], jwt.api_jwk.PyJWK)
        assert mock_decode.call_args.kwargs == {'algorithms': ['RS256']}

        assert user == 'test-user'
        assert token == 'test-token'


@pytest.mark.network
def test_get_jwks_client(jwks_client):
    assert 'urs.earthdata.nasa.gov' in jwks_client.uri


@pytest.mark.network
def test_bad_bearer_token(jwks_client):
    with pytest.raises(auth.InvalidTokenException, match=r'^Invalid authorization token provided'):
        auth.decode_edl_bearer_token('bad token', jwks_client)


def test_bad_asf_cookie(jwks_client, monkeypatch):
    with pytest.raises(auth.InvalidTokenException, match=r'^Invalid authorization cookie provided'):
        auth.decode_asf_cookie('bad token')


@pytest.fixture(scope='session')
def jwks_client():
    return auth.get_jwks_client()
