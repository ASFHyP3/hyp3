from datetime import datetime, timezone
from decimal import Decimal
from os import environ

from boto3.dynamodb.conditions import Key
from dateutil.parser import parse

from hyp3_api import handlers


def format_time(time: datetime):
    if time.tzinfo is None:
        raise ValueError(f'missing tzinfo for datetime {time}')
    utc_time = time.astimezone(timezone.utc)
    return utc_time.isoformat(timespec='seconds')


def get_remaining_jobs_for_user(user):
    previous_jobs = get_job_count_for_month(user)
    quota = int(environ['MONTHLY_JOB_QUOTA_PER_USER'])
    remaining_jobs = quota - previous_jobs
    return max(remaining_jobs, 0)


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


def convert_floats_to_decimals(element):
    if type(element) is float:
        return Decimal(element)
    if type(element) is list:
        return [convert_floats_to_decimals(item) for item in element]
    if type(element) is dict:
        return {key: convert_floats_to_decimals(value) for key, value in element.items()}
    return element
