from decimal import Decimal
from os import environ
from time import time
from uuid import uuid4

from boto3.dynamodb.conditions import Attr, Key
from connexion import context
from connexion.apps.flask_app import FlaskJSONEncoder
from flask import abort
from flask_cors import CORS
from hyp3_api import DYNAMODB_RESOURCE, connexion_app


class DecimalEncoder(FlaskJSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o == int(o):
                return int(o)
            return float(o)
        return super(DecimalEncoder, self).default(o)


def post_jobs(body, user):
    print(body)
    if not context['is_authorized']:
        abort(403)

    request_time = int(time())
    table = DYNAMODB_RESOURCE.Table(environ['TABLE_NAME'])

    for job in body['jobs']:
        job['job_id'] = str(uuid4())
        job['user_id'] = user
        job['status_code'] = 'PENDING'
        job['request_time'] = request_time
        table.put_item(Item=job)

    return body


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


connexion_app.app.json_encoder = DecimalEncoder
connexion_app.add_api('openapi-spec.yml', validate_responses=True, strict_validation=True)
CORS(connexion_app.app, origins=r'https?://([-\w]+\.)*asf\.alaska\.edu', supports_credentials=True)
