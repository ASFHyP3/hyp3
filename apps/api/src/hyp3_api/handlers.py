from http.client import responses

import requests
from flask import abort, jsonify, request

import dynamo
from dynamo.exceptions import InsufficientCreditsError, UnapprovedUserError
from hyp3_api import util
from hyp3_api.validation import GranuleValidationError, validate_jobs


def problem_format(status, message):
    response = jsonify({
        'status': status,
        'detail': message,
        'title': responses[status],
        'type': 'about:blank'
    })
    response.headers['Content-Type'] = 'application/problem+json'
    response.status_code = status
    return response


def post_jobs(body, user):
    print(body)

    try:
        validate_jobs(body['jobs'])
    except requests.HTTPError as e:
        print(f'WARN: CMR search failed: {e}')
    except GranuleValidationError as e:
        abort(problem_format(400, str(e)))

    try:
        body['jobs'] = dynamo.jobs.put_jobs(user, body['jobs'], dry_run=body.get('validate_only'))
    except UnapprovedUserError as e:
        abort(problem_format(403, str(e)))
    except InsufficientCreditsError as e:
        abort(problem_format(400, str(e)))
    return body


def get_jobs(user, start=None, end=None, status_code=None, name=None, job_type=None, start_token=None):
    try:
        start_key = util.deserialize(start_token) if start_token else None
    except util.TokenDeserializeError:
        abort(problem_format(400, 'Invalid start_token value'))
    jobs, last_evaluated_key = dynamo.jobs.query_jobs(user, start, end, status_code, name, job_type, start_key)
    payload = {'jobs': jobs}
    if last_evaluated_key is not None:
        next_token = util.serialize(last_evaluated_key)
        payload['next'] = util.build_next_url(request.url, next_token, request.headers.get('X-Forwarded-Host'),
                                              request.root_path)
    return payload


def get_job_by_id(job_id):
    job = dynamo.jobs.get_job(job_id)
    if job is None:
        abort(problem_format(404, f'job_id does not exist: {job_id}'))
    return job


def post_user(body: dict, user: str, edl_access_token: str) -> dict:
    print(body)
    return dynamo.user.create_user_application(user, edl_access_token, body)


def get_user(user):
    user_record = dynamo.user.get_or_create_user(user)
    return _user_response(user_record)


def _user_response(user_record: dict) -> dict:
    # TODO: count this as jobs are submitted, not every time `/user` is queried
    job_names = _get_names_for_user(user_record['user_id'])
    payload = {key: user_record[key] for key in user_record if not key.startswith('_')}
    payload['job_names'] = job_names
    return payload


def _get_names_for_user(user):
    jobs, next_key = dynamo.jobs.query_jobs(user)
    while next_key is not None:
        new_jobs, next_key = dynamo.jobs.query_jobs(user, start_key=next_key)
        jobs.extend(new_jobs)
    names = {job['name'] for job in jobs if 'name' in job}
    return sorted(list(names))
