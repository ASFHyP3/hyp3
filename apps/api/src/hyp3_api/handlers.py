import json
from http.client import responses
from pathlib import Path
from typing import Optional
from uuid import UUID

import boto3
import requests
from botocore.exceptions import BotoCoreError
from flask import abort, jsonify, request
from jsonschema import draft4_format_checker

import dynamo
from hyp3_api import util
from hyp3_api.validation import GranuleValidationError, validate_jobs

S3_CLIENT = boto3.client('s3')


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

    try:
        body['jobs'] = dynamo.jobs.put_jobs(user, body['jobs'], dry_run=body.get('validate_only'))
    except dynamo.jobs.InsufficientCreditsError as e:
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


def get_stac_item_from_job(job: dict) -> Optional[dict]:
    job_files = job.get('files')
    if job_files is None:
        return None

    product = job_files[0]
    stac_key = product['s3']['key'].replace(Path(product['filename']).suffix, '.json')

    try:
        response = S3_CLIENT.get_object(Bucket=product['s3']['bucket'], Key=stac_key)
    except S3_CLIENT.exceptions.NoSuchKey as e:
        abort(problem_format(404, f'STAC item does not exist for {job["job_id"]}'))
    # FIXME: No trust.
    except Exception as e:
        abort(problem_format(404, f'Woops. {e}'))

    stac_item = json.loads(response['Body'].read().decode('utf-8'))
    return stac_item


def get_stac_items_from_jobs(jobs: dict) -> dict:
    stac_items = [get_stac_item_from_job(job)for job in jobs['jobs']]
    return {
        'type': 'FeatureCollection',
        'features': stac_items,
        'links': [{
            'rel': 'next',
            'type': 'application/geo+json',
            'method': 'GET',
            'href': jobs['next'].replace('/jobs?', '/stac?')
        }]
    }


def get_names_for_user(user):
    jobs, next_key = dynamo.jobs.query_jobs(user)
    while next_key is not None:
        new_jobs, next_key = dynamo.jobs.query_jobs(user, start_key=next_key)
        jobs.extend(new_jobs)
    names = {job['name'] for job in jobs if 'name' in job}
    return sorted(list(names))


def get_user(user):
    user_record = dynamo.user.get_or_create_user(user)
    return {
        'user_id': user,
        'remaining_credits': user_record['remaining_credits'],
        # TODO: count this as jobs are submitted, not every time `/user` is queried
        'job_names': get_names_for_user(user)
    }
