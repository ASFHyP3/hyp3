import json
from datetime import datetime, timezone
from decimal import Decimal
from os import environ
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from boto3.dynamodb.conditions import Attr, Key

import dynamo.user
from dynamo.util import DYNAMODB_RESOURCE, convert_floats_to_decimals, format_time, get_request_time_expression

costs_file = Path(__file__).parent / 'costs.json'
COSTS = convert_floats_to_decimals(json.loads(costs_file.read_text()))

default_params_file = Path(__file__).parent / 'default_params_by_job_type.json'
if default_params_file.exists():
    DEFAULT_PARAMS_BY_JOB_TYPE = json.loads(default_params_file.read_text())
else:
    # Allows mocking with unittest.mock.patch
    DEFAULT_PARAMS_BY_JOB_TYPE = {}


class UnapprovedUserError(Exception):
    """Raised when trying to submit jobs as an unapproved user."""


class InsufficientCreditsError(Exception):
    """Raised when trying to submit jobs whose total cost exceeds the user's remaining credits."""


def put_jobs(user_id: str, jobs: List[dict], dry_run=False) -> List[dict]:
    table = DYNAMODB_RESOURCE.Table(environ['JOBS_TABLE_NAME'])
    request_time = format_time(datetime.now(timezone.utc))

    user_record = dynamo.user.get_or_create_user(user_id)
    if environ['REQUIRE_USER_APPROVAL'] == 'true' and not user_record['approved']:
        # TODO: include instructions for how to apply
        raise UnapprovedUserError(f'User {user_id} is not approved for processing')

    remaining_credits = user_record['remaining_credits']
    priority_override = user_record.get('priority_override')

    total_cost = Decimal('0.0')
    prepared_jobs = []
    for job in jobs:
        prepared_job = _prepare_job_for_database(
            job=job,
            user_id=user_id,
            request_time=request_time,
            remaining_credits=remaining_credits,
            priority_override=priority_override,
            running_cost=total_cost,
        )
        prepared_jobs.append(prepared_job)
        total_cost += prepared_job['credit_cost']

    if remaining_credits is not None and total_cost > remaining_credits:
        raise InsufficientCreditsError(
            f'These jobs would cost {total_cost} credits, but you have only {remaining_credits} remaining.'
        )

    assert prepared_jobs[-1]['priority'] >= 0
    if not dry_run:
        if remaining_credits is not None:
            dynamo.user.decrement_credits(user_id, total_cost)
        with table.batch_writer() as batch:
            for prepared_job in prepared_jobs:
                batch.put_item(Item=convert_floats_to_decimals(prepared_job))

    return prepared_jobs


def _prepare_job_for_database(
        job: dict,
        user_id: str,
        request_time: str,
        remaining_credits: Optional[Decimal],
        priority_override: Optional[int],
        running_cost: Decimal,
) -> dict:
    if priority_override:
        priority = priority_override
    elif remaining_credits is None:
        priority = 0
    else:
        priority = min(round(remaining_credits - running_cost), 9999)
    prepared_job = {
        'job_id': str(uuid4()),
        'user_id': user_id,
        'status_code': 'PENDING',
        'execution_started': False,
        'request_time': request_time,
        'priority': priority,
        **job,
    }
    if 'job_type' in prepared_job:
        prepared_job['job_parameters'] = {
            **DEFAULT_PARAMS_BY_JOB_TYPE[prepared_job['job_type']],
            **prepared_job.get('job_parameters', {})
        }
        prepared_job['credit_cost'] = _get_credit_cost(prepared_job, COSTS)
    else:
        prepared_job['credit_cost'] = Decimal('1.0')
    return prepared_job


def _get_credit_cost(job: dict, costs: list[dict]) -> Decimal:
    job_type = job['job_type']
    for cost_definition in costs:
        if cost_definition['job_type'] == job_type:

            if cost_definition.keys() not in ({'job_type', 'cost_parameter', 'cost_table'}, {'job_type', 'cost'}):
                raise ValueError(f'Cost definition for job type {job_type} has invalid keys: {cost_definition.keys()}')

            if 'cost_parameter' in cost_definition:
                cost_parameter = cost_definition['cost_parameter']
                parameter_value = job['job_parameters'][cost_parameter]
                for item in cost_definition['cost_table']:
                    if item['parameter_value'] == parameter_value:
                        return item['cost']
                raise ValueError(f'Cost not found for job type {job_type} with {cost_parameter} == {parameter_value}')

            return cost_definition['cost']
    raise ValueError(f'Cost not found for job type {job_type}')


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
