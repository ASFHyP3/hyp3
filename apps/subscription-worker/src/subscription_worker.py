from copy import deepcopy
from datetime import datetime, timedelta, timezone

import asf_search
import dateutil.parser

import dynamo
from lambda_logging import log_exceptions, logger


def get_processed_granules(user_id, name, job_type):
    processed_granules = []
    params = {'user': user_id, 'name': name, 'job_type': job_type}
    while True:
        jobs, next_token = dynamo.jobs.query_jobs(**params)
        granules = [job['job_parameters']['granules'][0] for job in jobs]
        processed_granules.extend(granules)
        if next_token is None:
            break
        params['start_key'] = next_token
    return processed_granules


def get_unprocessed_granules(subscription):
    processed_granules = get_processed_granules(
        subscription['user_id'],
        subscription['job_specification']['name'],
        subscription['job_specification']['job_type'],
    )

    search_results = asf_search.search(**subscription['search_parameters'])
    search_results.raise_if_incomplete()
    return [result for result in search_results if result.properties['sceneName'] not in processed_granules]


def get_neighbors(granule, depth, platform):
    stack = asf_search.baseline_search.stack_from_product(granule)
    stack.raise_if_incomplete()
    stack = [item for item in stack if
             item.properties['temporalBaseline'] < 0 and item.properties['sceneName'].startswith(platform)]
    neighbors = [item.properties['sceneName'] for item in stack[-depth:]]
    return neighbors


def get_jobs_for_granule(subscription, granule):
    job_specification = deepcopy(subscription['job_specification'])
    if 'job_parameters' not in job_specification:
        job_specification['job_parameters'] = {}
    job_specification['subscription_id'] = subscription['subscription_id']

    job_type = job_specification['job_type']

    if job_type in ['RTC_GAMMA', 'WATER_MAP']:
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


def get_jobs_for_subscription(subscription, limit):
    granules = get_unprocessed_granules(subscription)
    jobs = []
    for granule in granules[:limit]:
        jobs.extend(get_jobs_for_granule(subscription, granule))
    return jobs


def disable_subscription(subscription):
    subscription['enabled'] = False
    dynamo.subscriptions.put_subscription(subscription['user_id'], subscription)


def handle_subscription(subscription):
    jobs = get_jobs_for_subscription(subscription, limit=20)
    if jobs:
        logger.info(f'Submitting {len(jobs)} jobs')
        dynamo.jobs.put_jobs(subscription['user_id'], jobs, fail_when_over_quota=False)


@log_exceptions
def lambda_handler(event, context) -> None:
    subscription = event['subscription']
    logger.info(f'Handling subscription {subscription["subscription_id"]} for user {subscription["user_id"]}')

    if not subscription['enabled']:
        raise ValueError(f'subscription {subscription["subscription_id"]} is disabled')

    handle_subscription(subscription)

    cutoff_date = datetime.now(tz=timezone.utc) - timedelta(days=5)
    logger.info(f'Cutoff date: {cutoff_date.isoformat()}')

    end_date = dateutil.parser.parse(subscription['search_parameters']['end'])
    logger.info(f'Subscription end date: {end_date.isoformat()}')

    unprocessed_granule_count = len(get_unprocessed_granules(subscription))
    logger.info(f'Unprocessed granules: {unprocessed_granule_count}')

    if end_date <= cutoff_date and unprocessed_granule_count == 0:
        logger.info(f'Disabling subscription {subscription["subscription_id"]}')
        disable_subscription(subscription)
