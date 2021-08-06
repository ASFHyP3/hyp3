from os import environ
from uuid import uuid4

from boto3.dynamodb.conditions import Key

from dynamo.util import DYNAMODB_RESOURCE


def put_subscription(user, subscription):
    subscription = {
        'subscription_id': str(uuid4()),
        'user_id': user,
        **subscription
    }
    table = DYNAMODB_RESOURCE.Table(environ['SUBSCRIPTIONS_TABLE_NAME'])
    table.put_item(Item=subscription)
    return subscription


def get_subscriptions_for_user(user):
    table = DYNAMODB_RESOURCE.Table(environ['SUBSCRIPTIONS_TABLE_NAME'])
    params = {
     'IndexName': 'user_id',
     'KeyConditionExpression': Key('user_id').eq(user),
    }
    response = table.query(**params)
    subscriptions = response['Items']
    while 'LastEvaluatedKey' in response:
        params['ExclusiveStartKey'] = response['LastEvaluatedKey']
        response = table.query(**params)
        subscriptions.extend(response['Items'])
    return subscriptions


def get_all_subscriptions():
    table = DYNAMODB_RESOURCE.Table(environ['SUBSCRIPTIONS_TABLE_NAME'])

    response = table.scan()
    subscriptions = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        subscriptions.extend(response['Items'])
    return subscriptions
