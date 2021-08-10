import itertools
import uuid

import asf_search

import dynamo


class QuotaError(Exception):
    """User is at quota and cannot submit more jobs'"""


def get_unprocessed_granules(subscription):
    search_parameters = subscription['search_parameters']
    search_results = asf_search.search(**search_parameters)
    all_granules = [product.properties['sceneName'] for product in search_results]

    processed_jobs, _ = dynamo.jobs.query_jobs(
        user=subscription['user_id'],
        name=subscription['job_specification']['name'],
        job_type=subscription['job_specification']['job_type'],
    )
    processed_granules = itertools.chain(*[job['job_parameters']['granules'] for job in processed_jobs])
    return list(set(all_granules) - set(processed_granules))


def get_payload_for_job(subscription, granule):
    payload = subscription['job_specification']
    if 'job_parameters' not in payload:
        payload['job_parameters'] = {}
    payload['job_parameters']['granules'] = [granule]
    return payload


def submit_jobs_for_granule(subscription, granule):
    payload = [
        get_payload_for_job(subscription, granule)
    ]
    dynamo.jobs.put_jobs(subscription['user_id'], payload)


def handle_subscription(subscription):
    granules = get_unprocessed_granules(subscription)
    for granule in granules:
        try:
            submit_jobs_for_granule(subscription, granule)
        except QuotaError:
            break


def lambda_handler(event, context):
    subscriptions = dynamo.subscriptions.get_all_subscriptions()
    for subscription in subscriptions:
        handle_subscription(subscription)
