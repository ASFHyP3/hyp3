from os import environ

import jwt


class InvalidTokenException(Exception):
    """Raised when authorization token cannot be decoded."""


def decode_edl_bearer_token(token: str, jwks_client: jwt.PyJWKClient) -> tuple[str, str]:
    signing_key = jwks_client.get_signing_key('edljwtpubkey_ops')
    try:
        payload = jwt.decode(token, signing_key, algorithms=['RS256'])
    except jwt.exceptions.InvalidTokenError as e:
        raise InvalidTokenException(f'Invalid authorization token provided: {str(e)}')
    return payload['uid'], token


def decode_asf_cookie(cookie: str) -> tuple[str, str]:
    try:
        payload = jwt.decode(cookie, environ['AUTH_PUBLIC_KEY'], algorithms=environ['AUTH_ALGORITHM'])
    except jwt.exceptions.InvalidTokenError as e:
        raise InvalidTokenException(f'Invalid authorization cookie provided: {str(e)}')
    return payload['urs-user-id'], payload['urs-access-token']


def get_jwks_client() -> jwt.PyJWKClient:
    return jwt.PyJWKClient('https://urs.earthdata.nasa.gov/.well-known/edl_ops_jwks.json')
