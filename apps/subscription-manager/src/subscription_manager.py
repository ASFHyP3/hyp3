import json
import os

import boto3

import dynamo

LAMBDA_CLIENT = boto3.client('lambda')


def invoke_worker(worker_function_arn: str, subscription: dict) -> None:
    payload = {'subscription': subscription}
    print(f'Invoking worker for subscription {subscription["subscription_id"]}')
    response = LAMBDA_CLIENT.invoke(
        FunctionName=worker_function_arn,
        InvocationType='Event',
        Payload=json.dumps(payload),
    )
    print(f'Got response status code {response["StatusCode"]} for subscription {subscription["subscription_id"]}')


def lambda_handler(event, context):
    worker_function_arn = os.environ['SUBSCRIPTION_WORKER_ARN']
    subscriptions = dynamo.subscriptions.get_all_subscriptions()
    enabled_subscriptions = [subscription for subscription in subscriptions if subscription['enabled']]
    for subscription in enabled_subscriptions:
        invoke_worker(worker_function_arn, subscription)
