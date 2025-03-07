import binascii
import json
from base64 import b64decode, b64encode
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


class TokenDeserializeError(Exception):
    """Raised when paging results and `start_token` fails to deserialize."""


def get_granules(jobs: list[dict]) -> set[str]:
    return {
        granule
        for key in ['granules', 'reference', 'secondary']
        for job in jobs
        for granule in job['job_parameters'].get(key, [])
    }


def serialize(payload: dict) -> str:
    string_version = json.dumps(payload)
    base_64 = b64encode(string_version.encode())
    return base_64.decode()


def deserialize(token: str) -> Any:
    try:
        string_version = b64decode(token.encode())
        return json.loads(string_version)
    except (json.JSONDecodeError, binascii.Error, UnicodeDecodeError):
        raise TokenDeserializeError


def build_next_url(url: str, start_token: str, x_forwarded_host: str | None = None, root_path: str = '') -> str:
    url_parts = list(urlparse(url))

    if x_forwarded_host:
        url_parts[1] = x_forwarded_host

    if root_path:
        url_parts[2] = url_parts[2].removeprefix(root_path)

    query = dict(parse_qsl(url_parts[4]))
    query['start_token'] = start_token
    url_parts[4] = urlencode(query)

    return urlunparse(url_parts)
