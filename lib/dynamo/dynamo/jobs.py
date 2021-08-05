from os import environ
from typing import List

from boto3.dynamodb.conditions import Attr, Key

from dynamo.util import DYNAMODB_RESOURCE, get_request_time_expression


def put_jobs(payload: List[dict]):
    table = DYNAMODB_RESOURCE.Table(environ['JOBS_TABLE_NAME'])

    for item in payload:
        table.put_item(Item=item)


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
