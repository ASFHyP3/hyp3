import time
from os import environ

import jwt


def decode_token(token, required_scopes):
    try:
        payload = jwt.decode(token, environ['AUTH_PUBLIC_KEY'], algorithms=environ['AUTH_ALGORITHM'])
        return {
            'active': True,
            'sub': payload['urs-user-id'],
        }
    except (jwt.ExpiredSignatureError, jwt.DecodeError):
        return None


def get_mock_jwt_cookie(user, lifetime_in_seconds=100):
    payload = {
        'urs-user-id': user,
        'exp': int(time.time()) + lifetime_in_seconds,
    }
    value = jwt.encode(
        payload=payload,
        key=environ['AUTH_PUBLIC_KEY'],
        algorithm=environ['AUTH_ALGORITHM'],
    )
    return value
