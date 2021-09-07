from copy import deepcopy
from datetime import datetime, timedelta, timezone

import asf_search
import dateutil.parser

import dynamo


def get_unprocessed_granules(subscription):
    processed_jobs, _ = dynamo.jobs.query_jobs(
        user=subscription['user_id'],
        name=subscription['job_specification']['name'],
        job_type=subscription['job_specification']['job_type'],
    )
    processed_granules = [job['job_parameters']['granules'][0] for job in processed_jobs]

    search_results = asf_search.search(**subscription['search_parameters'])
    return [result for result in search_results if result.properties['sceneName'] not in processed_granules]


def get_neighbors(granule, depth, platform):
    stack = asf_search.baseline_search.stack_from_product(granule)
    stack = [item for item in stack if
             item.properties['temporalBaseline'] < 0 and item.properties['sceneName'].startswith(platform)]
    neighbors = [item.properties['sceneName'] for item in stack[-depth:]]
    return neighbors


def get_jobs_for_granule(subscription, granule):
    job_specification = subscription['job_specification']
    if 'job_parameters' not in job_specification:
        job_specification['job_parameters'] = {}
    job_specification['subscription_id'] = subscription['subscription_id']

    job_type = job_specification['job_type']

    if job_type in ['RTC_GAMMA']:
        job_specification['job_parameters']['granules'] = [granule.properties['sceneName']]
        payload = [job_specification]
    elif job_type in ['AUTORIFT', 'INSAR_GAMMA']:
        payload = []
        neighbors = get_neighbors(granule, 2, subscription['search_parameters']['platform'])
        for neighbor in neighbors:
            job = deepcopy(job_specification)
            job['job_parameters']['granules'] = [granule.properties['sceneName'], neighbor]
            payload.append(job)
    else:
        raise ValueError(f'Subscription job type {job_type} not supported')
    return payload


def get_jobs_for_subscription(subscription):
    granules = get_unprocessed_granules(subscription)
    jobs = []
    for granule in granules:
        jobs.extend(get_jobs_for_granule(subscription, granule))
    return jobs


def disable_subscription(subscription):
    subscription['enabled'] = False
    dynamo.subscriptions.put_subscription(subscription['user_id'], subscription)


def handle_subscription(subscription):
    jobs = get_jobs_for_subscription(subscription)
    if jobs:
        dynamo.jobs.put_jobs(subscription['user_id'], jobs, fail_when_over_quota=False)


def lambda_handler(event, context):
    subscriptions = dynamo.subscriptions.get_all_subscriptions()
    for subscription in subscriptions:
        end_filter = datetime.now(tz=timezone.utc) - timedelta(days=5)
        if subscription['enabled']:
            handle_subscription(subscription)

            if end_filter > dateutil.parser.parse(subscription['search_parameters']['end']):
                disable_subscription(subscription)
