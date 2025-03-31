import json
from decimal import Decimal
from os import environ
from pathlib import Path
from uuid import uuid4

import botocore.exceptions
from boto3.dynamodb.conditions import Attr, Key

import dynamo.user
from dynamo.exceptions import (
    DatabaseConditionException,
    InsufficientCreditsError,
    InvalidApplicationStatusError,
    NotStartedApplicationError,
    PendingApplicationError,
    RejectedApplicationError,
    UpdateJobForDifferentUserError,
    UpdateJobNotFoundError,
)
from dynamo.user import APPLICATION_APPROVED, APPLICATION_NOT_STARTED, APPLICATION_PENDING, APPLICATION_REJECTED
from dynamo.util import DYNAMODB_RESOURCE, convert_floats_to_decimals, current_utc_time, get_request_time_expression


costs_file = Path(__file__).parent / 'costs.json'
COSTS = convert_floats_to_decimals(json.loads(costs_file.read_text()))

default_params_file = Path(__file__).parent / 'default_params_by_job_type.json'
if default_params_file.exists():
    DEFAULT_PARAMS_BY_JOB_TYPE = json.loads(default_params_file.read_text())
else:
    # Allows mocking with unittest.mock.patch
    DEFAULT_PARAMS_BY_JOB_TYPE = {}


def put_jobs(user_id: str, jobs: list[dict], dry_run: bool = False) -> list[dict]:
    table = DYNAMODB_RESOURCE.Table(environ['JOBS_TABLE_NAME'])
    request_time = current_utc_time()

    user_record = dynamo.user.get_or_create_user(user_id)

    _raise_for_application_status(user_record['application_status'], user_record['user_id'])

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


def _raise_for_application_status(application_status: str, user_id: str) -> None:
    if application_status == APPLICATION_NOT_STARTED:
        raise NotStartedApplicationError(user_id)
    if application_status == APPLICATION_PENDING:
        raise PendingApplicationError(user_id)
    if application_status == APPLICATION_REJECTED:
        raise RejectedApplicationError(user_id)
    if application_status != APPLICATION_APPROVED:
        raise InvalidApplicationStatusError(user_id, application_status)


def _prepare_job_for_database(
    job: dict,
    user_id: str,
    request_time: str,
    remaining_credits: Decimal | None,
    priority_override: int | None,
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
            **prepared_job.get('job_parameters', {}),
        }
        prepared_job['credit_cost'] = _get_credit_cost(prepared_job, COSTS)
    else:
        prepared_job['credit_cost'] = Decimal('1.0')
    return prepared_job


def _get_credit_cost(job: dict, costs: dict) -> Decimal:
    job_type = job['job_type']
    cost_definition = costs[job_type]

    if cost_definition.keys() not in ({'cost_parameters', 'cost_table'}, {'cost'}):
        raise ValueError(f'Cost definition for job type {job_type} has invalid keys: {cost_definition.keys()}')

    if 'cost' in cost_definition:
        cost = cost_definition['cost']
    else:
        cost = _get_cost_from_table(job, cost_definition)

    if not isinstance(cost, Decimal):
        raise ValueError(f'Job type {job["job_type"]} has non-Decimal cost value')

    return cost


def _get_cost_from_table(job: dict, cost_definition: dict) -> Decimal:
    cost_lookup = cost_definition['cost_table']

    for cost_parameter in cost_definition['cost_parameters']:
        parameter_value = _get_cost_parameter_value(job, cost_parameter)

        try:
            cost_lookup = cost_lookup[parameter_value]
        except KeyError:
            raise ValueError(
                f'Cost not found for job type {job["job_type"]} with {cost_parameter} == {parameter_value}'
            )

    return cost_lookup


def _get_cost_parameter_value(job: dict, cost_parameter: str) -> str:
    parameter_value = job['job_parameters'][cost_parameter]

    if isinstance(parameter_value, str):
        cost_parameter_value = parameter_value

    elif isinstance(parameter_value, int):
        cost_parameter_value = str(parameter_value)

    elif isinstance(parameter_value, float):
        cost_parameter_value = str(int(parameter_value))

    elif isinstance(parameter_value, list):
        cost_parameter_value = str(len(parameter_value))

    else:
        raise ValueError(
            f'Cost parameter {cost_parameter} for job type {job["job_type"]} has '
            f'unsupported type {type(parameter_value)}'
        )

    return cost_parameter_value


def query_jobs(
    user: str,
    start: str | None = None,
    end: str | None = None,
    status_code: str | None = None,
    name: str | None = None,
    job_type: str | None = None,
    start_key: dict | None = None,
) -> tuple[list[dict], dict | None]:
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


def get_job(job_id: str) -> dict:
    table = DYNAMODB_RESOURCE.Table(environ['JOBS_TABLE_NAME'])
    response = table.get_item(Key={'job_id': job_id})
    return response.get('Item')


def update_job(job: dict) -> None:
    """Update the job as it progresses through its execution."""
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


# TODO:
#  - add dynamo and api tests for updating name when the job doesn't have one
#  - allow updating arbitrary fields? and handle name=None as special case?
def update_job_for_user(job_id: str, name: str | None, user_id: str) -> dict:
    """Update the user's job at their request."""
    if name is not None:
        update_expression = 'SET #name = :name'
        name_value = {':name': name}
    else:
        update_expression = 'REMOVE #name'
        name_value = {}

    table = DYNAMODB_RESOURCE.Table(environ['JOBS_TABLE_NAME'])
    try:
        job = table.update_item(
            Key={'job_id': job_id},
            UpdateExpression=update_expression,
            ConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id, **name_value},
            ExpressionAttributeNames={'#name': 'name'},
            ReturnValues='ALL_NEW',
            ReturnValuesOnConditionCheckFailure='ALL_OLD',
        )['Attributes']
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            if 'Item' not in e.response:
                raise UpdateJobNotFoundError(f'Job {job_id} does not exist')
            if e.response['Item']['user_id']['S'] != user_id:
                raise UpdateJobForDifferentUserError("You cannot modify a different user's job")
            # TODO test:
            raise DatabaseConditionException(
                f"Updating job {job_id} for user {user_id} failed the condition check, but the job's user_id is correct"
            )
        raise

    return job


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
