from datetime import datetime, timezone
from decimal import Decimal
from os import environ
from pathlib import Path
from uuid import UUID, uuid4

import requests
from connexion import problem
from connexion.apps.flask_app import FlaskJSONEncoder
from flask import jsonify, make_response, redirect, request
from flask_cors import CORS
from jsonschema import draft4_format_checker

from hyp3_api import connexion_app, dynamo, util
from hyp3_api.openapi import get_spec
from hyp3_api.validation import GranuleValidationError, validate_jobs


class DecimalEncoder(FlaskJSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o == int(o):
                return int(o)
            return float(o)
        return super(DecimalEncoder, self).default(o)


@draft4_format_checker.checks('uuid')
def is_uuid(val):
    try:
        UUID(val, version=4)
    except ValueError:
        return False
    return True


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


@connexion_app.app.route('/')
def redirect_to_ui():
    return redirect('/ui')


def post_jobs(body, user):
    print(body)

    monthly_quota = get_max_jobs_per_month(user)
    remaining_jobs = util.get_remaining_jobs_for_user(user, monthly_quota)
    if remaining_jobs - len(body['jobs']) < 0:
        message = f'Your monthly quota is {monthly_quota} jobs. You have {remaining_jobs} jobs remaining.'
        return problem(400, 'Bad Request', message)

    try:
        validate_jobs(body['jobs'])
    except requests.HTTPError as e:
        print(f'WARN: CMR search failed: {e}')
    except GranuleValidationError as e:
        return problem(400, 'Bad Request', str(e))

    request_time = util.format_time(datetime.now(timezone.utc))
    jobs = []
    for job in body['jobs']:
        job['job_id'] = str(uuid4())
        job['user_id'] = user
        job['status_code'] = 'PENDING'
        job['request_time'] = request_time
        jobs.append(util.convert_floats_to_decimals(job))
    if not body.get('validate_only'):
        dynamo.put_jobs(jobs)
    return body


def get_jobs(user, start=None, end=None, status_code=None, name=None, job_type=None, start_token=None):
    try:
        start_key = util.deserialize(start_token) if start_token else None
    except util.TokenDeserializeError:
        return problem(400, 'Bad Request', 'Invalid start_token value')
    jobs, last_evaluated_key = dynamo.query_jobs(user, start, end, status_code, name, job_type, start_key)
    payload = {'jobs': jobs}
    if last_evaluated_key is not None:
        next_token = util.serialize(last_evaluated_key)
        payload['next'] = util.set_start_token(request.url, next_token)
    return payload


def get_job_by_id(job_id):
    job = dynamo.get_job(job_id)
    if job is None:
        return problem(404, 'Not Found', f'job_id does not exist: {job_id}')
    return job


def get_names_for_user(user):
    jobs, next_key = dynamo.query_jobs(user)
    while next_key is not None:
        new_jobs, next_key = dynamo.query_jobs(user, start_key=next_key)
        jobs.extend(new_jobs)
    names = {job['name'] for job in jobs if 'name' in job}
    return sorted(list(names))


def get_max_jobs_per_month(user):
    user = dynamo.get_user(user)
    if user:
        max_jobs_per_month = user['max_jobs_per_month']
    else:
        max_jobs_per_month = int(environ['MONTHLY_JOB_QUOTA_PER_USER'])
    return max_jobs_per_month


def get_user(user):
    max_jobs = get_max_jobs_per_month(user)

    return {
        'user_id': user,
        'quota': {
            'max_jobs_per_month': max_jobs,
            'remaining': util.get_remaining_jobs_for_user(user, max_jobs),
        },
        'job_names': get_names_for_user(user)
    }


api_spec_file = Path(__file__).parent / 'api-spec' / 'openapi-spec.yml'
api_spec = get_spec(api_spec_file)
connexion_app.app.json_encoder = DecimalEncoder
connexion_app.add_api(api_spec, strict_validation=True)
CORS(connexion_app.app, origins=r'https?://([-\w]+\.)*asf\.alaska\.edu', supports_credentials=True)
