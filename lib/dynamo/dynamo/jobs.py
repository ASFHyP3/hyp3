from datetime import datetime, timezone
from os import environ
from typing import List
from uuid import uuid4

from boto3.dynamodb.conditions import Attr, Key

from dynamo.user import get_max_jobs_per_month
from dynamo.util import DYNAMODB_RESOURCE, convert_floats_to_decimals, format_time, get_request_time_expression


class QuotaError(Exception):
    """Raised when trying to submit more jobs that user has remaining"""


def _get_job_count_for_month(user):
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    job_count_for_month = count_jobs(user, format_time(start_of_month))
    return job_count_for_month


def get_remaining_jobs_for_user(user, limit):
    previous_jobs = _get_job_count_for_month(user)
    remaining_jobs = limit - previous_jobs
    return max(remaining_jobs, 0)


def put_jobs(user_id: str, jobs: List[dict], fail_when_over_quota=True) -> List[dict]:
    table = DYNAMODB_RESOURCE.Table(environ['JOBS_TABLE_NAME'])
    request_time = format_time(datetime.now(timezone.utc))

    job_limit = get_max_jobs_per_month(user_id)
    number_of_jobs = len(jobs)
    remaining_jobs = get_remaining_jobs_for_user(user_id, job_limit)
    if number_of_jobs > remaining_jobs:
        if fail_when_over_quota:
            raise QuotaError(f'Your monthly quota is {job_limit} jobs. You have {remaining_jobs} jobs remaining.')
        jobs = jobs[:remaining_jobs]

    prepared_jobs = [
        {
            'job_id': str(uuid4()),
            'user_id': user_id,
            'status_code': 'PENDING',
            'request_time': request_time,
            **job,
        } for job in jobs
    ]

    for prepared_job in prepared_jobs:
        table.put_item(Item=convert_floats_to_decimals(prepared_job))
    return prepared_jobs


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
    update_expression = 'SET {}'.format(','.join(f'{k}=:{k}' for k in job if k != primary_key))
    expression_attribute_values = {f':{k}': v for k, v in job.items() if k != primary_key}
    table.update_item(
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values,
    )


def get_jobs_by_status_code(status_code: str, limit: int) -> List[dict]:
    table = DYNAMODB_RESOURCE.Table(environ['JOBS_TABLE_NAME'])
    response = table.query(
        IndexName='status_code',
        KeyConditionExpression=Key('status_code').eq(status_code),
        Limit=limit,
    )
    jobs = response['Items']
    return jobs
