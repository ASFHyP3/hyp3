from os import environ
from uuid import UUID

import requests
from flask import abort, jsonify, request
from jsonschema import draft4_format_checker

import dynamo
from hyp3_api import util
from hyp3_api.validation import GranuleValidationError, validate_jobs


def problem_format(status, title, message):
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
        abort(problem_format(400, 'Bad Request', message))

    try:
        validate_jobs(body['jobs'])
    except requests.HTTPError as e:
        print(f'WARN: CMR search failed: {e}')
    except GranuleValidationError as e:
        abort(problem_format(400, 'Bad Request', str(e)))

    if not body.get('validate_only'):
        body['jobs'] = dynamo.jobs.put_jobs(user, body['jobs'])
    return body


def get_jobs(user, start=None, end=None, status_code=None, name=None, job_type=None, start_token=None):
    try:
        start_key = util.deserialize(start_token) if start_token else None
    except util.TokenDeserializeError:
        abort(problem_format(400, 'Bad Request', 'Invalid start_token value'))
    jobs, last_evaluated_key = dynamo.jobs.query_jobs(user, start, end, status_code, name, job_type, start_key)
    payload = {'jobs': jobs}
    if last_evaluated_key is not None:
        next_token = util.serialize(last_evaluated_key)
        payload['next'] = util.set_start_token(request.url, next_token)
    return payload


def get_job_by_id(job_id):
    job = dynamo.jobs.get_job(job_id)
    if job is None:
        abort(problem_format(404, 'Not Found', f'job_id does not exist: {job_id}'))
    return job


def get_names_for_user(user):
    jobs, next_key = dynamo.jobs.query_jobs(user)
    while next_key is not None:
        new_jobs, next_key = dynamo.jobs.query_jobs(user, start_key=next_key)
        jobs.extend(new_jobs)
    names = {job['name'] for job in jobs if 'name' in job}
    return sorted(list(names))


def get_max_jobs_per_month(user):
    user = dynamo.user.get_user(user)
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


def post_subscriptions(body, user):
    return dynamo.subscriptions.put_subscription(user, body)


def get_subscriptions(user):
    return dynamo.subscriptions.get_subscriptions_for_user(user)
