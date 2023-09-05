from datetime import datetime, timezone
from os import environ
from typing import Callable, List, Optional, Union
from uuid import uuid4

from boto3.dynamodb.conditions import Attr, Key

import dynamo.user
from dynamo.util import DYNAMODB_RESOURCE, convert_floats_to_decimals, format_time, get_request_time_expression


class QuotaError(Exception):
    """Raised when trying to submit more jobs that user has remaining"""


def _get_job_count_for_month(user) -> int:
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    job_count_for_month = count_jobs(user, format_time(start_of_month))
    return job_count_for_month


def get_quota_status(user) -> Union[tuple[int, int, int], tuple[None, None, None]]:
    max_jobs = dynamo.user.get_max_jobs_per_month(user)

    if max_jobs is not None:
        previous_jobs = _get_job_count_for_month(user)
        remaining_jobs = max(max_jobs - previous_jobs, 0)
    else:
        previous_jobs = None
        remaining_jobs = None

    return max_jobs, previous_jobs, remaining_jobs


def put_jobs(user_id: str, jobs: List[dict], fail_when_over_quota=True) -> List[dict]:
    table = DYNAMODB_RESOURCE.Table(environ['JOBS_TABLE_NAME'])
    request_time = format_time(datetime.now(timezone.utc))

    max_jobs, previous_jobs, remaining_jobs = get_quota_status(user_id)
    has_quota = max_jobs is not None
    if has_quota:
        assert previous_jobs is not None
        assert remaining_jobs is not None

    if has_quota and len(jobs) > remaining_jobs:
        if fail_when_over_quota:
            raise QuotaError(f'Your monthly quota is {max_jobs} jobs. You have {remaining_jobs} jobs remaining.')
        jobs = jobs[:remaining_jobs]

    priority_override = dynamo.user.get_priority(user_id)
    priority = _get_job_priority(priority_override, has_quota)

    prepared_jobs = [
        {
            'job_id': str(uuid4()),
            'user_id': user_id,
            'status_code': 'PENDING',
            'execution_started': False,
            'request_time': request_time,
            'priority': priority(previous_jobs, index),
            **job,
        } for index, job in enumerate(jobs)
    ]

    for prepared_job in prepared_jobs:
        table.put_item(Item=convert_floats_to_decimals(prepared_job))
    return prepared_jobs


def _get_job_priority(priority_override: Optional[int], has_quota: bool) -> Callable[[Optional[int], int], int]:
    if priority_override is not None:
        priority = lambda _, __: priority_override
    elif has_quota:
        priority = lambda previous_jobs, job_index: max(9999 - previous_jobs - job_index, 0)
    else:
        priority = lambda _, __: 0
    return priority


def count_jobs(user, start=None, end=None):
    table = DYNAMODB_RESOURCE.Table(environ['JOBS_TABLE_NAME'])
    key_expression = Key('user_id').eq(user)
    if start is not None or end is not None:
        key_expression &= get_request_time_expression(start, end)

    params = {
        'IndexName': 'user_id',
        'KeyConditionExpression': key_expression,
        'Select': 'COUNT',
    }
    response = table.query(**params)
    job_count = response['Count']
    while 'LastEvaluatedKey' in response:
        params['ExclusiveStartKey'] = response['LastEvaluatedKey']
        response = table.query(**params)
        job_count += response['Count']
    return job_count


def query_jobs(user, start=None, end=None, status_code=None, name=None, job_type=None, start_key=None):
    table = DYNAMODB_RESOURCE.Table(environ['JOBS_TABLE_NAME'])

    key_expression = Key('user_id').eq(user)
    if start is not None or end is not None:
        key_expression &= get_request_time_expression(start, end)

    filter_expression = Attr('job_id').exists()
    if status_code is not None:
        filter_expression &= Attr('status_code').eq(status_code)
    if name is not None:
        filter_expression &= Attr('name').eq(name)
    if job_type is not None:
        filter_expression &= Attr('job_type').eq(job_type)

    params = {
        'IndexName': 'user_id',
        'KeyConditionExpression': key_expression,
        'FilterExpression': filter_expression,
        'ScanIndexForward': False,
    }
    if start_key is not None:
        params['ExclusiveStartKey'] = start_key

    response = table.query(**params)
    jobs = response['Items']
    return jobs, response.get('LastEvaluatedKey')


def get_job(job_id):
    table = DYNAMODB_RESOURCE.Table(environ['JOBS_TABLE_NAME'])
    response = table.get_item(Key={'job_id': job_id})
    return response.get('Item')


def update_job(job):
    table = DYNAMODB_RESOURCE.Table(environ['JOBS_TABLE_NAME'])
    primary_key = 'job_id'
    key = {'job_id': job[primary_key]}

    prepared_job = convert_floats_to_decimals(job)
    update_expression = 'SET {}'.format(','.join(f'{k}=:{k}' for k in prepared_job if k != primary_key))
    expression_attribute_values = {f':{k}': v for k, v in prepared_job.items() if k != primary_key}

    table.update_item(
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values,
    )


def get_jobs_waiting_for_execution(limit: int) -> list[dict]:
    table = DYNAMODB_RESOURCE.Table(environ['JOBS_TABLE_NAME'])

    params = {
        'IndexName': 'status_code',
        'KeyConditionExpression': Key('status_code').eq('PENDING'),
        'FilterExpression': Attr('execution_started').ne(True),
    }
    response = table.query(**params)
    jobs = response['Items']

    while 'LastEvaluatedKey' in response and len(jobs) < limit:
        params['ExclusiveStartKey'] = response['LastEvaluatedKey']
        response = table.query(**params)
        jobs.extend(response['Items'])

    return jobs[:limit]
