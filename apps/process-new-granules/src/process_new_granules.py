import itertools
import uuid

import asf_search

import dynamo


class QuotaError(Exception):
    """User is at quota and cannot submit more jobs'"""


def get_unprocessed_granules(subscription):
    search_results = asf_search.search(**subscription['search_parameters'])
    all_granules = [product.properties['sceneName'] for product in search_results]

    processed_jobs = dynamo.jobs.query_jobs(
        subscription['user_id'],
        job_type=subscription['job_specification']['job_type'],
        name=subscription['job_specification']['name']
    )
    processed_granules = itertools.chain([job['job_parameters']['granules'] for job in processed_jobs])
    return list(set(all_granules) - set(processed_granules))


def get_payload_for_job(subscription, granule):
    payload = subscription['job_specification']
    if 'job_parameters' not in payload:
        payload['job_parameters'] = {}
    payload['job_id'] = str(uuid.uuid4())
    payload['user_id'] = subscription['user_id']
    payload['status_code'] = 'PENDING'
    payload['job_parameters']['granules'] = [granule]
    return payload


def submit_jobs_for_granule(subscription, granule):
    payload = [
        get_payload_for_job(subscription, granule)
    ]
    dynamo.jobs.put_jobs(payload)


def handle_subscription(subscription):
    granules = get_unprocessed_granules(subscription)
    for granule in granules:
        try:
            submit_jobs_for_granule(subscription, granule)
        except QuotaError:
            break


def lambda_handler(event, contect):
    subscriptions = dynamo.subscriptions.get_all_subscriptions()
    for subscription in subscriptions:
        handle_subscription(subscription)
