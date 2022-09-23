import os

import boto3

import dynamo


def invoke_worker(worker_function_arn: str, subscription: dict) -> None:
    payload = {'subscription': subscription}
    client = boto3.client('lambda')
    response = client.invoke(
        FunctionName=worker_function_arn,
        InvocationType='Event',
        Payload=payload,
    )
    # TODO attempt to log worker success or failure?


def lambda_handler(event, context):
    # TODO populate this env var with the correct arn
    worker_function_arn = os.environ['SUBSCRIPTIONS_WORKER_ARN']
    subscriptions = dynamo.subscriptions.get_all_subscriptions()
    enabled_subscriptions = [subscription for subscription in subscriptions if subscription['enabled']]
    for subscription in enabled_subscriptions:
        # TODO is it worth having the worker just take sub id and re-fetch the subscription object, in case it's updated?
        invoke_worker(worker_function_arn, subscription)
