import json
import logging
import os

import boto3

import dynamo

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

LAMBDA_CLIENT = boto3.client('lambda')


def invoke_worker(worker_function_arn: str, subscription: dict) -> dict:
    payload = json.dumps(
        {'subscription': dynamo.util.convert_decimals_to_numbers(subscription)}
    )
    return LAMBDA_CLIENT.invoke(
        FunctionName=worker_function_arn,
        InvocationType='Event',
        Payload=payload,
    )


def lambda_handler(event, context):
    worker_function_arn = os.environ['SUBSCRIPTION_WORKER_ARN']
    logger.info(f'Worker function ARN: {worker_function_arn}')

    subscriptions = dynamo.subscriptions.get_all_subscriptions()
    logger.info(f'Got {len(subscriptions)} subscriptions')

    enabled_subscriptions = [subscription for subscription in subscriptions if subscription['enabled']]
    logger.info(f'Got {len(enabled_subscriptions)} enabled subscriptions')

    for count, subscription in enumerate(enabled_subscriptions, start=1):
        logger.info(
            f'({count}/{len(enabled_subscriptions)}) '
            f'Invoking worker for subscription {subscription["subscription_id"]}'
        )
        response = invoke_worker(worker_function_arn, subscription)
        logger.info(f'Got response status code {response["StatusCode"]} for subscription {subscription["subscription_id"]}')
