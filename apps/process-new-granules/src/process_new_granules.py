import itertools
from copy import deepcopy
from datetime import datetime, timedelta, timezone

import asf_search
import dateutil.parser

import dynamo


class QuotaError(Exception):
    """User is at quota and cannot submit more jobs'"""


def get_unprocessed_granules(subscription):
    search_results = asf_search.search(**subscription['search_parameters'])
    all_granules = [product.properties['sceneName'] for product in search_results]

    processed_jobs, _ = dynamo.jobs.query_jobs(
        user=subscription['user_id'],
        name=subscription['job_specification']['name'],
        job_type=subscription['job_specification']['job_type'],
    )
    #  TODO This line could be made a lot clearer.
    processed_granules = itertools.chain(*[job['job_parameters']['granules'][0] for job in processed_jobs])
    return list(set(all_granules) - set(processed_granules))


def get_neighbors(granule, depth, platform):
    reference = asf_search.search(granule_list=granule, processingLevel='SLC')[0]
    stack = asf_search.baseline_search.stack_from_product(reference)
    stack = [item for item in stack if
             item.properties['temporalBaseline'] < 0 and item.properties['sceneName'].startwith(platform)]
    neighbors = [item.properties['sceneName'] for item in stack[-depth:]]
    return neighbors


def get_payload_for_job(subscription, granule):
    job_specification = subscription['job_specification']
    if 'job_parameters' not in job_specification:
        job_specification['job_parameters'] = {}

    job_type = subscription['job_specification']['job_type']

    if job_type in ['RTC_GAMMA']:
        job_specification['job_parameters']['granules'] = [granule]
        payload = [job_specification]
    elif job_type in ['AUTORIFT', 'INSAR_GAMMA']:
        payload = []
        neighbors = get_neighbors(granule, 2, subscription['search_parameters']['platform'])
        for neighbor in neighbors:
            job = deepcopy(job_specification)
            job['job_parameters']['granules'] = [granule, neighbor]
            payload.append(job)
    else:
        raise ValueError(f'Subscription job type {job_type} not supported')
    return payload


def submit_jobs_for_granule(subscription, granule):
    payload = get_payload_for_job(subscription, granule)
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
        end_filter = datetime.now(tz=timezone.utc) - timedelta(days=5)
        if end_filter <= dateutil.parser.parse(subscription['search_parameters']['end']):
            handle_subscription(subscription)
