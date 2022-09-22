import os
from datetime import datetime, timedelta, timezone

import boto3

import dynamo


def handle_subscription_batch(subscriptions: list[dict], cutoff_date: datetime, worker_function_arn: str) -> None:
    payload = {
        'subscriptions': subscriptions,
        'cutoff_date': cutoff_date.isoformat(),
    }
    client = boto3.client('lambda')
    response = client.invoke(
        FunctionName=worker_function_arn,
        InvocationType='Event',
        Payload=payload,
    )
    # TODO attempt to log worker success or failure?


def lambda_handler(event, context):
    # TODO populate this env var with the correct arn
    worker_function_arn = os.environ['PROCESS_NEW_GRANULES_WORKER_ARN']
    subscriptions = dynamo.subscriptions.get_all_subscriptions()
    cutoff_date = datetime.now(tz=timezone.utc) - timedelta(days=5)
    enabled_subscriptions = [subscription for subscription in subscriptions if subscription['enabled']]
    batch_size = 3
    for i in range(0, len(enabled_subscriptions), batch_size):
        handle_subscription_batch(subscriptions[i:i+batch_size], cutoff_date, worker_function_arn)
