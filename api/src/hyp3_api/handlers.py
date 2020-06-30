from datetime import datetime
from decimal import Decimal
from os import environ
from uuid import uuid4

import pytz
from boto3.dynamodb.conditions import Attr, Key
from connexion import context, problem
from connexion.apps.flask_app import FlaskJSONEncoder
from dateutil.parser import parse
from flask_cors import CORS
from hyp3_api import DYNAMODB_RESOURCE, connexion_app


class DecimalEncoder(FlaskJSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o == int(o):
                return int(o)
            return float(o)
        return super(DecimalEncoder, self).default(o)


class QuotaError(Exception):
    pass


def post_jobs(body, user):
    print(body)
    if not context['is_authorized']:
        return problem(403, 'Forbidden', f'User {user} does not have permission to submit jobs.')

    try:
        check_quota_for_user(user, len(body['jobs']))
    except QuotaError as e:
        return problem(400, 'Bad Request', str(e))

    request_time = datetime.utcnow().isoformat(timespec='seconds') + 'Z'
    table = DYNAMODB_RESOURCE.Table(environ['TABLE_NAME'])

    for job in body['jobs']:
        job['job_id'] = str(uuid4())
        job['user_id'] = user
        job['status_code'] = 'PENDING'
        job['request_time'] = request_time
        table.put_item(Item=job)

    return body


def get_jobs(user, start=None, status_code=None):
    table = DYNAMODB_RESOURCE.Table(environ['TABLE_NAME'])

    key_expression = Key('user_id').eq(user)
    if start is not None:
        datetime_start = parse(start)
        utc_start = convert_to_utc(datetime_start)
        key_expression &= Key('request_time').gte(utc_start.isoformat(timespec='seconds'))

    filter_expression = Attr('job_id').exists()
    if status_code is not None:
        filter_expression &= Attr('status_code').eq(status_code)

    response = table.query(
        IndexName='user_id',
        KeyConditionExpression=key_expression,
        FilterExpression=filter_expression,
    )

    return {'jobs': response['Items']}


def convert_to_utc(time: datetime):
    if time.tzinfo is not None:
        return time.astimezone(pytz.UTC)
    else:
        return time


def check_quota_for_user(user, number_of_jobs):
    previous_jobs = get_job_count_for_month(user)
    quota = int(environ['MONTHLY_JOB_QUOTA_PER_USER'])
    job_count = previous_jobs + number_of_jobs
    if job_count > quota:
        raise QuotaError(f'Your monthly quota is {quota} jobs. You have {quota - previous_jobs} jobs remaining.')


def get_job_count_for_month(user):
    now = datetime.utcnow()
    start_of_month = datetime(year=now.year, month=now.month, day=1)
    response = get_jobs(user, start_of_month.isoformat(timespec='seconds'))
    return len(response['jobs'])


connexion_app.app.json_encoder = DecimalEncoder
connexion_app.add_api('openapi-spec.yml', validate_responses=True, strict_validation=True)
CORS(connexion_app.app, origins=r'https?://([-\w]+\.)*asf\.alaska\.edu', supports_credentials=True)
