from datetime import datetime, timezone
from decimal import Decimal
from os import environ
from pathlib import Path
from uuid import uuid4

import requests
from boto3.dynamodb.conditions import Attr, Key
from connexion import problem
from connexion.apps.flask_app import FlaskJSONEncoder
from flask import jsonify, make_response
from flask_cors import CORS

from hyp3_api import DYNAMODB_RESOURCE, connexion_app
from hyp3_api.openapi import get_spec
from hyp3_api.util import convert_floats_to_decimals, format_time, get_remaining_jobs_for_user, \
    get_request_time_expression
from hyp3_api.validation import GranuleValidationError, validate_jobs


class DecimalEncoder(FlaskJSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o == int(o):
                return int(o)
            return float(o)
        return super(DecimalEncoder, self).default(o)


@connexion_app.app.before_request
def check_system_available():
    if environ['SYSTEM_AVAILABLE'] != "true":
        message = 'HyP3 is currently unavailable. Please try again later.'
        error = {
            'detail': message,
            'status': 503,
            'title': 'Service Unavailable',
            'type': 'about:blank'
        }
        return make_response(jsonify(error), 503)


def post_jobs(body, user):
    print(body)

    quota = get_user(user)['quota']
    if quota['remaining'] - len(body['jobs']) < 0:
        message = f'Your monthly quota is {quota["max_jobs_per_month"]} jobs. You have {quota["remaining"]} jobs remaining.'
        return problem(400, 'Bad Request', message)

    try:
        validate_jobs(body['jobs'])
    except requests.HTTPError as e:
        print(f'WARN: CMR search failed: {e}')
    except GranuleValidationError as e:
        return problem(400, 'Bad Request', str(e))

    request_time = format_time(datetime.now(timezone.utc))
    table = DYNAMODB_RESOURCE.Table(environ['JOBS_TABLE_NAME'])

    for job in body['jobs']:
        job['job_id'] = str(uuid4())
        job['user_id'] = user
        job['status_code'] = 'PENDING'
        job['request_time'] = request_time
        if not body.get('validate_only'):
            job = convert_floats_to_decimals(job)
            table.put_item(Item=job)

    return body


def get_jobs(user, start=None, end=None, status_code=None, name=None):
    table = DYNAMODB_RESOURCE.Table(environ['JOBS_TABLE_NAME'])

    key_expression = Key('user_id').eq(user)
    if start is not None or end is not None:
        key_expression &= get_request_time_expression(start, end)

    filter_expression = Attr('job_id').exists()
    if status_code is not None:
        filter_expression &= Attr('status_code').eq(status_code)
    if name is not None:
        filter_expression &= Attr('name').eq(name)

    response = table.query(
        IndexName='user_id',
        KeyConditionExpression=key_expression,
        FilterExpression=filter_expression,
    )
    return {'jobs': response['Items']}


def get_names_for_user(user):
    table = DYNAMODB_RESOURCE.Table(environ['JOBS_TABLE_NAME'])
    key_expression = Key('user_id').eq(user)
    response = table.query(
        IndexName='user_id',
        KeyConditionExpression=key_expression,
    )
    names = {record['name'] for record in response['Items'] if 'name' in record}
    return sorted(list(names))


def get_max_jobs_per_month(user):
    table = DYNAMODB_RESOURCE.Table(environ['USERS_TABLE_NAME'])
    response = table.get_item(Key={'user_id': user})
    if 'Item' in response:
        max_jobs_per_month = response['Item']['max_jobs_per_month']
    else:
        max_jobs_per_month = int(environ['MONTHLY_JOB_QUOTA_PER_USER'])
    return max_jobs_per_month


def get_user(user):
    max_jobs = get_max_jobs_per_month(user)

    return {
        'user_id': user,
        'quota': {
            'max_jobs_per_month': max_jobs,
            'remaining': get_remaining_jobs_for_user(user, max_jobs),
        },
        'job_names': get_names_for_user(user)
    }


api_spec_file = Path(__file__).parent / 'api-spec' / 'openapi-spec.yml'
api_spec = get_spec(api_spec_file)
connexion_app.app.json_encoder = DecimalEncoder
connexion_app.add_api(api_spec, validate_responses=True, strict_validation=True)
CORS(connexion_app.app, origins=r'https?://([-\w]+\.)*asf\.alaska\.edu', supports_credentials=True)
