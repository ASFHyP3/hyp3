from http.client import responses

from flask import Response, abort, jsonify, request

import dynamo
from dynamo.exceptions import (
    AccessCodeError,
    InsufficientCreditsError,
    UnexpectedApplicationStatusError,
    UpdateJobForDifferentUserError,
    UpdateJobNotFoundError,
)
from hyp3_api import util
from hyp3_api.multi_burst_validation import MultiBurstValidationError
from hyp3_api.validation import CmrError, ValidationError, validate_jobs


def problem_format(status: int, message: str) -> Response:
    response = jsonify({'status': status, 'detail': message, 'title': responses[status], 'type': 'about:blank'})
    response.headers['Content-Type'] = 'application/problem+json'
    response.status_code = status
    return response


def post_jobs(body: dict, user: str) -> dict:
    print(body)

    try:
        validate_jobs(body['jobs'])
    except CmrError as e:
        abort(problem_format(503, str(e)))
    except (ValidationError, MultiBurstValidationError) as e:
        abort(problem_format(400, str(e)))

    try:
        body['jobs'] = dynamo.jobs.put_jobs(user, body['jobs'], dry_run=bool(body.get('validate_only')))
    except UnexpectedApplicationStatusError as e:
        abort(problem_format(403, str(e)))
    except InsufficientCreditsError as e:
        abort(problem_format(400, str(e)))
    return body


def get_jobs(
    user: str,
    start: str | None = None,
    end: str | None = None,
    status_code: str | None = None,
    name: str | None = None,
    job_type: str | None = None,
    start_token: str | None = None,
) -> dict:
    try:
        start_key = util.deserialize(start_token) if start_token else None
    except util.TokenDeserializeError:
        abort(problem_format(400, 'Invalid start_token value'))
    jobs, last_evaluated_key = dynamo.jobs.query_jobs(user, start, end, status_code, name, job_type, start_key)
    payload: dict = {'jobs': jobs}
    if last_evaluated_key is not None:
        next_token = util.serialize(last_evaluated_key)
        payload['next'] = util.build_next_url(
            request.url, next_token, request.headers.get('X-Forwarded-Host'), request.root_path
        )
    return payload


def get_job_by_id(job_id: str) -> dict:
    job = dynamo.jobs.get_job(job_id)
    if job is None:
        abort(problem_format(404, f'job_id does not exist: {job_id}'))
    return job


def patch_job_by_id(body: dict, job_id: str, user: str) -> dict:
    try:
        job = dynamo.jobs.update_job_for_user(job_id, body['name'], user)
    except UpdateJobForDifferentUserError as e:
        abort(problem_format(403, str(e)))
    except UpdateJobNotFoundError as e:
        abort(problem_format(404, str(e)))
    return job


# TODO: need to return anything?
def patch_jobs(body: dict, user: str) -> None:
    # TODO: handle errors
    dynamo.jobs.update_jobs_for_user(body['job_ids'], body['name'], user)


def patch_user(body: dict, user: str, edl_access_token: str) -> dict:
    print(body)
    try:
        user_record = dynamo.user.update_user(user, edl_access_token, body)
    except AccessCodeError as e:
        abort(problem_format(403, str(e)))
    except UnexpectedApplicationStatusError as e:
        abort(problem_format(403, str(e)))
    return _user_response(user_record)


def get_user(user: str) -> dict:
    user_record = dynamo.user.get_or_create_user(user)
    return _user_response(user_record)


def _user_response(user_record: dict) -> dict:
    # TODO: count this as jobs are submitted, not every time `/user` is queried
    job_names = _get_names_for_user(user_record['user_id'])
    payload = {key: user_record[key] for key in user_record if not key.startswith('_')}
    payload['job_names'] = job_names
    return payload


def _get_names_for_user(user: str) -> list[str]:
    jobs, next_key = dynamo.jobs.query_jobs(user)
    while next_key is not None:
        new_jobs, next_key = dynamo.jobs.query_jobs(user, start_key=next_key)
        jobs.extend(new_jobs)
    names = {job['name'] for job in jobs if 'name' in job}
    return sorted(list(names))
