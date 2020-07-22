from datetime import datetime, timezone
from decimal import Decimal
from os import environ
from uuid import uuid4

import requests
from boto3.dynamodb.conditions import Attr, Key
from connexion import problem
from connexion.apps.flask_app import FlaskJSONEncoder
from flask_cors import CORS
from hyp3_api import DYNAMODB_RESOURCE, connexion_app
from hyp3_api.util import format_time, get_remaining_jobs_for_user,\
    get_request_time_expression
from hyp3_api.validation import CmrError, check_granules_exist


class DecimalEncoder(FlaskJSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o == int(o):
                return int(o)
            return float(o)
        return super(DecimalEncoder, self).default(o)


def post_jobs(body, user):
    print(body)

    quota = get_user(user)['quota']
    if quota['remaining'] - len(body['jobs']) < 0:
        message = f'Your monthly quota is {quota["limit"]} jobs. You have {quota["remaining"]} jobs remaining.'
        return problem(400, 'Bad Request', message)

    try:
        granules = [job['job_parameters']['granule'] for job in body['jobs']]
        check_granules_exist(granules)
    except requests.HTTPError as e:
        print(f'WARN: CMR search failed: {e}')
    except CmrError as e:
        return problem(400, 'Bad Request', str(e))

    request_time = format_time(datetime.now(timezone.utc))
    table = DYNAMODB_RESOURCE.Table(environ['TABLE_NAME'])

    for job in body['jobs']:
        job['job_id'] = str(uuid4())
        job['user_id'] = user
        job['status_code'] = 'PENDING'
        job['request_time'] = request_time
        table.put_item(Item=job)

    return body


def get_jobs(user, start=None, end=None, status_code=None):
    table = DYNAMODB_RESOURCE.Table(environ['TABLE_NAME'])

    key_expression = Key('user_id').eq(user)
    if start is not None or end is not None:
        key_expression &= get_request_time_expression(start, end)

    filter_expression = Attr('job_id').exists()
    if status_code is not None:
        filter_expression &= Attr('status_code').eq(status_code)

    response = table.query(
        IndexName='user_id',
        KeyConditionExpression=key_expression,
        FilterExpression=filter_expression,
    )
    return {'jobs': response['Items']}


def get_user(user):
    return {
        'user_id': user,
        'quota': {
            'limit': int(environ['MONTHLY_JOB_QUOTA_PER_USER']),
            'remaining': get_remaining_jobs_for_user(user),
        },
    }


connexion_app.app.json_encoder = DecimalEncoder
connexion_app.add_api('openapi-spec.yml', validate_responses=True, strict_validation=True)
CORS(connexion_app.app, origins=r'https?://([-\w]+\.)*asf\.alaska\.edu', supports_credentials=True)
