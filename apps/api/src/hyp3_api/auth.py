import time
from os import environ

import jwt


def decode_token(token: str | None) -> dict | None:
    if token is None:
        return None
    try:
        jwks_client = jwt.PyJWKClient('https://urs.earthdata.nasa.gov/.well-known/edl_ops_jwks.json')
        signing_key = jwks_client.get_signing_key('edljwtpubkey_ops')
        return jwt.decode(token, signing_key, algorithms=['RS256'])
    except (jwt.ExpiredSignatureError, jwt.DecodeError):
        return None


def get_mock_jwt_cookie(user: str, lifetime_in_seconds: int, access_token: str) -> str:
    payload = {
        'urs-user-id': user,
        'urs-access-token': access_token,
        'exp': int(time.time()) + lifetime_in_seconds,
    }
    value = jwt.encode(
        payload=payload,
        key=environ['AUTH_PUBLIC_KEY'],
        algorithm=environ['AUTH_ALGORITHM'],
    )
    return value
