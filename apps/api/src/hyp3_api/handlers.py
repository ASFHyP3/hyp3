from datetime import datetime, timezone
from os import environ
from uuid import UUID, uuid4

import requests
from flask import abort, jsonify, request
from jsonschema import draft4_format_checker

from hyp3_api import dynamo, util
from hyp3_api.validation import GranuleValidationError, validate_jobs


def error(status, title, message):
    response = jsonify({
        'status': status,
        'detail': message,
        'title': title,
        'type': 'about:blank'
    })
    response.headers['Content-Type'] = 'application/problem+json'
    response.status_code = status
    return response


@draft4_format_checker.checks('uuid')
def is_uuid(val):
    try:
        UUID(val, version=4)
    except ValueError:
        return False
    return True


def post_jobs(body, user):
    print(body)

    monthly_quota = get_max_jobs_per_month(user)
    remaining_jobs = util.get_remaining_jobs_for_user(user, monthly_quota)
    if remaining_jobs - len(body['jobs']) < 0:
        message = f'Your monthly quota is {monthly_quota} jobs. You have {remaining_jobs} jobs remaining.'
        abort(error(400, 'Bad Request', message))

    try:
        validate_jobs(body['jobs'])
    except requests.HTTPError as e:
        print(f'WARN: CMR search failed: {e}')
    except GranuleValidationError as e:
        abort(error(400, 'Bad Request', str(e)))

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
        abort(error(400, 'Bad Request', 'Invalid start_token value'))
    jobs, last_evaluated_key = dynamo.query_jobs(user, start, end, status_code, name, job_type, start_key)
    payload = {'jobs': jobs}
    if last_evaluated_key is not None:
        next_token = util.serialize(last_evaluated_key)
        payload['next'] = util.set_start_token(request.url, next_token)
    return payload


def get_job_by_id(job_id):
    job = dynamo.get_job(job_id)
    if job is None:
        abort(error(404, 'Not Found', f'job_id does not exist: {job_id}'))
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
