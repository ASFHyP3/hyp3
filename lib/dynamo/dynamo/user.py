from os import environ

from dynamo.util import DYNAMODB_RESOURCE


def get_user(user):
    table = DYNAMODB_RESOURCE.Table(environ['USERS_TABLE_NAME'])
    response = table.get_item(Key={'user_id': user})
    return response.get('Item')
