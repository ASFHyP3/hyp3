from os import environ

from boto3.dynamodb.conditions import Key

from dynamo import DYNAMODB_RESOURCE


def put_subscription(subscription):
    table = DYNAMODB_RESOURCE.Table(environ['SUBSCRIPTIONS_TABLE_NAME'])
    table.put_item(Item=subscription)


def get_subscriptions(user):
    table = DYNAMODB_RESOURCE.Table(environ['SUBSCRIPTIONS_TABLE_NAME'])
    params = {
     'IndexName': 'user_id',
     'KeyConditionExpression': Key('user_id').eq(user),
    }
    response = table.query(**params)
    return response['Items']
