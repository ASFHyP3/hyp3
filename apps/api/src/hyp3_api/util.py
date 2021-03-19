import json
from base64 import b64encode, b64decode
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

from hyp3_api import handlers


def get_granules(jobs):
    granules = set()
    for job in jobs:
        for granule in job['job_parameters']['granules']:
            granules.add(granule)
    return granules


def format_time(time: datetime):
    if time.tzinfo is None:
        raise ValueError(f'missing tzinfo for datetime {time}')
    utc_time = time.astimezone(timezone.utc)
    return utc_time.isoformat(timespec='seconds')


def get_remaining_jobs_for_user(user, limit):
    previous_jobs = get_job_count_for_month(user)
    remaining_jobs = limit - previous_jobs
    return max(remaining_jobs, 0)


def get_job_count_for_month(user):
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    response = handlers.get_jobs(user, format_time(start_of_month))
    return len(response['jobs'])


def convert_floats_to_decimals(element):
    if type(element) is float:
        return Decimal(element)
    if type(element) is list:
        return [convert_floats_to_decimals(item) for item in element]
    if type(element) is dict:
        return {key: convert_floats_to_decimals(value) for key, value in element.items()}
    return element


def build_next_token(next_token):
    string_version = json.dumps(next_token)
    base_64 = b64encode(string_version.encode())
    return base_64.decode()


def decode_start_token(start_token: str):
    string_version = b64decode(start_token.encode())
    return json.loads(string_version)


def set_start_token(url, start_token):
    url_parts = list(urlparse(url))
    query = parse_qsl(url_parts[4])
    query.append(('start_token', start_token))
    url_parts[4] = urlencode(query)
    return urlunparse(url_parts)