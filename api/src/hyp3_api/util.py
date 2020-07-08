from datetime import datetime, timezone
from os import environ

import requests
from boto3.dynamodb.conditions import Key
from dateutil.parser import parse
from hyp3_api import CMR_URL, handlers


class QuotaError(Exception):
    pass


class CmrError(Exception):
    pass


def format_time(time: datetime):
    if time.tzinfo is None:
        raise ValueError(f'missing tzinfo for datetime {time}')
    utc_time = time.astimezone(timezone.utc)
    return utc_time.isoformat(timespec='seconds')


def check_quota_for_user(user, number_of_jobs):
    previous_jobs = get_job_count_for_month(user)
    quota = int(environ['MONTHLY_JOB_QUOTA_PER_USER'])
    job_count = previous_jobs + number_of_jobs
    if job_count > quota:
        raise QuotaError(f'Your monthly quota is {quota} jobs. You have {quota - previous_jobs} jobs remaining.')


def get_job_count_for_month(user):
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    response = handlers.get_jobs(user, format_time(start_of_month))
    return len(response['jobs'])


def get_request_time_expression(start, end):
    key = Key('request_time')
    formatted_start = (format_time(parse(start)) if start else None)
    formatted_end = (format_time(parse(end)) if end else None)

    if formatted_start and formatted_end:
        return key.between(formatted_start, formatted_end)
    if formatted_start:
        return key.gte(formatted_start)
    if formatted_end:
        return key.lte(formatted_end)


def check_granules_exist(granules):
    cmr_parameters = {
        'producer_granule_id': granules,
        'provider': 'ASF',
        'collection_concept_ids': {
            "C1214470488-ASF",  # SENTINEL-1A_SLC
            "C1327985661-ASF",  # SENTINEL-1B_SLC
        }
    }
    response = requests.get(CMR_URL, params=cmr_parameters)
    response.raise_for_status()
    found_granules = [entry['producer_granule_id'] for entry in response.json()['feed']['entry']]
    not_found_granules = set(granules) - set(found_granules)
    if not_found_granules:
        raise CmrError(f'Some requested scenes could not be found: {",".join(not_found_granules)}')
