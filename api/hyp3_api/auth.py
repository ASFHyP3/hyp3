import time
from os import environ

import jwt


def decode_token(token, required_scopes):
    return {
        'active': True
    }


def get_mock_jwt_cookie(user, expires_in=100):
    payload = {
        'urs-user-id': user,
        'exp': int(time.time()) + expires_in,
    }
    value = jwt.encode(
        payload=payload,
        key=environ['AUTH_PUBLIC_KEY'],
        algorithm=environ['AUTH_ALGORITHM'],
    )
    return value.decode()
