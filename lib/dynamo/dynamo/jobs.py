from datetime import datetime, timezone
from os import environ
from typing import List, Optional
from uuid import uuid4

from boto3.dynamodb.conditions import Attr, Key

import dynamo.user
from dynamo.util import DYNAMODB_RESOURCE, convert_floats_to_decimals, format_time, get_request_time_expression


class InsufficientCreditsError(Exception):
    """Raised when trying to submit jobs whose total cost exceeds the user's remaining credits."""


def get_credit_cost(job: dict) -> float:
    return 1.0


# TODO add/update tests
def put_jobs(user_id: str, jobs: List[dict], dry_run=False) -> List[dict]:
    table = DYNAMODB_RESOURCE.Table(environ['JOBS_TABLE_NAME'])
    request_time = format_time(datetime.now(timezone.utc))

    user_record = dynamo.user.get_user(user_id)
    if not user_record:
        user_record = dynamo.user.create_user(user_id)

    remaining_credits = user_record['remaining_credits']
    priority_override = user_record.get('priority_override')

    previous_job_priority = None
    prepared_jobs = []
    for job in jobs:
        prepared_job = prepare_job_for_database(
            job=job,
            user_id=user_id,
            request_time=request_time,
            remaining_credits=remaining_credits,
            priority_override=priority_override,
            previous_job_priority=previous_job_priority,
        )
        prepared_jobs.append(prepared_job)
        previous_job_priority = prepared_job['priority']

    total_cost = sum(job['credit_cost'] for job in prepared_jobs)
    if remaining_credits is not None and total_cost > remaining_credits:
        raise InsufficientCreditsError(
            f'These jobs would cost {total_cost} credits, but you have only {remaining_credits} remaining.'
        )

    if not dry_run:
        for prepared_job in prepared_jobs:
            table.put_item(Item=convert_floats_to_decimals(prepared_job))
        if remaining_credits is not None:
            # TODO: handle ValueError from decrement_credits? or just let it propagate?
            dynamo.user.decrement_credits(user_id, total_cost)

    return prepared_jobs


def prepare_job_for_database(
        job: dict,
        user_id: str,
        request_time: str,
        remaining_credits: Optional[float],
        priority_override: Optional[int],
        previous_job_priority: Optional[int],
) -> dict:
    credit_cost = get_credit_cost(job)
    if priority_override:
        priority = priority_override
    elif remaining_credits is None:
        priority = 0
    # TODO if you have > 9999 credits, you can get higher job priority by submitting jobs one at a time;
    #  are we OK with this behavior?
    elif previous_job_priority is None:
        priority = min(int(remaining_credits), 9999)
    else:
        # TODO should we raise exception if reach 0?
        priority = max(previous_job_priority - int(credit_cost), 0)
    return {
        'job_id': str(uuid4()),
        'user_id': user_id,
        'status_code': 'PENDING',
        'execution_started': False,
        'request_time': request_time,
        'credit_cost': credit_cost,
        'priority': priority,
        **job,
    }


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
