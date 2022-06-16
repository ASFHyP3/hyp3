from http.client import responses
from uuid import UUID

import requests
from flask import abort, jsonify, request
from jsonschema import draft4_format_checker

import dynamo
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


@draft4_format_checker.checks('uuid')
def is_uuid(val):
    try:
        UUID(val, version=4)
    except ValueError:
        return False
    return True


def post_jobs(body, user):
    print(body)

    try:
        validate_jobs(body['jobs'])
    except requests.HTTPError as e:
        print(f'WARN: CMR search failed: {e}')
    except GranuleValidationError as e:
        abort(problem_format(400, str(e)))

    if not body.get('validate_only'):
        try:
            body['jobs'] = dynamo.jobs.put_jobs(user, body['jobs'])
        except dynamo.jobs.QuotaError as e:
            abort(problem_format(400, str(e)))
        return body


def get_jobs(user, start=None, end=None, status_code=None, name=None, job_type=None, start_token=None,
             subscription_id=None):
    try:
        start_key = util.deserialize(start_token) if start_token else None
    except util.TokenDeserializeError:
        abort(problem_format(400, 'Invalid start_token value'))
    jobs, last_evaluated_key = dynamo.jobs.query_jobs(user, start, end, status_code, name, job_type, start_key,
                                                      subscription_id)
    payload = {'jobs': jobs}
    if last_evaluated_key is not None:
        next_token = util.serialize(last_evaluated_key)
        payload['next'] = util.build_next_url(request.url, next_token, request.headers.get('X-Forwarded-For'))
    return payload


def get_job_by_id(job_id):
    job = dynamo.jobs.get_job(job_id)
    if job is None:
        abort(problem_format(404, f'job_id does not exist: {job_id}'))
    return job


def get_names_for_user(user):
    jobs, next_key = dynamo.jobs.query_jobs(user)
    while next_key is not None:
        new_jobs, next_key = dynamo.jobs.query_jobs(user, start_key=next_key)
        jobs.extend(new_jobs)
    names = {job['name'] for job in jobs if 'name' in job}
    return sorted(list(names))


def get_user(user):
    max_jobs, _, remaining_jobs = dynamo.jobs.get_quota_status(user)

    return {
        'user_id': user,
        'quota': {
            'max_jobs_per_month': max_jobs,
            'remaining': remaining_jobs,
        },
        'job_names': get_names_for_user(user)
    }


def post_subscriptions(body, user):
    subscription = body['subscription']
    validate_only = body.get('validate_only')
    try:
        subscription = dynamo.subscriptions.put_subscription(user, subscription, validate_only)
        response = {
            'subscription': subscription
        }
        if validate_only is not None:
            response['validate_only'] = validate_only
        return response
    except ValueError as e:
        abort(problem_format(400, str(e)))


def get_subscriptions(user, name=None, job_type=None, enabled=None):
    subscriptions = dynamo.subscriptions.get_subscriptions_for_user(user, name, job_type, enabled)
    payload = {
        'subscriptions': subscriptions
    }
    return payload


def get_subscription_by_id(subscription_id):
    subscription = dynamo.subscriptions.get_subscription_by_id(subscription_id)
    if subscription is None:
        abort(problem_format(404, f'subscription_id does not exist: {subscription_id}'))
    return subscription


def patch_subscriptions(subscription_id, body, user):
    subscription = dynamo.subscriptions.get_subscription_by_id(subscription_id)
    if subscription is None:
        abort(problem_format(404, f'subscription_id does not exist: {subscription_id}'))

    if subscription['user_id'] != user:
        abort(problem_format(403, 'You may not update subscriptions created by a different user'))

    search_parameters = ['start', 'end', 'intersectsWith']
    for key in search_parameters:
        if key in body:
            subscription['search_parameters'][key] = body[key]

    if 'enabled' in body:
        subscription['enabled'] = body['enabled']

    try:
        dynamo.subscriptions.put_subscription(user, subscription)
    except ValueError as e:
        abort(problem_format(400, str(e)))

    return subscription
