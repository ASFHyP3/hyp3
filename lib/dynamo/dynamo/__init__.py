import boto3

DYNAMODB_RESOURCE = boto3.resource('dynamodb')

from dynamo import jobs, subscriptions, user

__all__ = [
    'DYNAMODB_RESOURCE',
    'jobs',
    'subscriptions',
    'user',
]
