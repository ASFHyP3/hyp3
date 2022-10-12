import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

import boto3

import dynamo

LOG: Optional[logging.LoggerAdapter] = None

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


def get_logger(request_id: str) -> logging.LoggerAdapter:
    format_str = '{asctime}\t{levelname}\tRequestId: {request_id}\t{message}'

    logging.basicConfig(level=logging.INFO, format=format_str, style='{')
    logging.Formatter.formatTime = (
        lambda self, record, datefmt=None: datetime.fromtimestamp(record.created, timezone.utc).isoformat()
    )

    return logging.LoggerAdapter(logger=logging.getLogger(), extra={'request_id': request_id})


def lambda_handler(event, context):
    global LOG
    LOG = get_logger(context.aws_request_id)

    worker_function_arn = os.environ['SUBSCRIPTION_WORKER_ARN']
    LOG.info(f'Worker function ARN: {worker_function_arn}')

    subscriptions = dynamo.subscriptions.get_all_subscriptions()
    LOG.info(f'Got {len(subscriptions)} subscriptions')

    enabled_subscriptions = [subscription for subscription in subscriptions if subscription['enabled']]
    LOG.info(f'Got {len(enabled_subscriptions)} enabled subscriptions')

    for count, subscription in enumerate(enabled_subscriptions, start=1):
        LOG.info(
            f'({count}/{len(enabled_subscriptions)}) '
            f'Invoking worker for subscription {subscription["subscription_id"]}'
        )
        response = invoke_worker(worker_function_arn, subscription)
        LOG.info(
            f'Got response status code {response["StatusCode"]} for subscription {subscription["subscription_id"]}'
        )
