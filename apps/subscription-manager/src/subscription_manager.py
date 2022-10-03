import json
import os

import boto3

import dynamo

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
    print(f'Worker function ARN: {worker_function_arn}')

    subscriptions = dynamo.subscriptions.get_all_subscriptions()
    print(f'Got {len(subscriptions)} subscriptions')

    enabled_subscriptions = [subscription for subscription in subscriptions if subscription['enabled']]
    print(f'Got {len(enabled_subscriptions)} enabled subscriptions')

    for count, subscription in enumerate(enabled_subscriptions, start=1):
        print(
            f'({count}/{len(enabled_subscriptions)}) '
            f'Invoking worker for subscription {subscription["subscription_id"]}'
        )
        response = invoke_worker(worker_function_arn, subscription)
        print(f'Got response status code {response["StatusCode"]} for subscription {subscription["subscription_id"]}')
