import json
from os import environ

from boto3.dynamodb.conditions import Attr, Key
from connexion import context
from flask import abort
from flask_cors import CORS
from hyp3_api import DYNAMODB_RESOURCE, STEP_FUNCTION_CLIENT, connexion_app


def start_execution(payload):
    job = STEP_FUNCTION_CLIENT.start_execution(
        stateMachineArn=environ['STEP_FUNCTION_ARN'],
        input=json.dumps(payload, sort_keys=True),
    )
    job_id = job['executionArn'].split(':')[-1]
    return job_id


def post_jobs(body, user):
    print(body)
    if not context['is_authorized']:
        abort(403)

    job_ids = []
    for job in body['jobs']:
        job['user_id'] = user
        job_id = start_execution(job)
        job_ids.append(job_id)

    return [{'job_id': job_id} for job_id in job_ids]


def get_jobs(user, status_code=None):
    table = DYNAMODB_RESOURCE.Table(environ['TABLE_NAME'])
    filter_expression = Attr('job_id').exists()
    if status_code is not None:
        filter_expression = filter_expression & Attr('status_code').eq(status_code)
    response = table.query(
        IndexName='user_id',
        KeyConditionExpression=Key('user_id').eq(user),
        FilterExpression=filter_expression,
    )
    return {'jobs': response['Items']}


connexion_app.add_api('openapi-spec.yml', validate_responses=True, strict_validation=True)
CORS(connexion_app.app, origins=r'https?://([-\w]+\.)*asf\.alaska\.edu', supports_credentials=True)
