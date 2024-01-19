from os import environ
from typing import Optional

from dynamo.util import DYNAMODB_RESOURCE


def get_user(user_id: str) -> Optional[dict]:
    table = DYNAMODB_RESOURCE.Table(environ['USERS_TABLE_NAME'])
    response = table.get_item(Key={'user_id': user_id})
    return response.get('Item')


def get_priority(user_id: str) -> Optional[int]:
    user = get_user(user_id)
    if user:
        priority = user.get('priority')
    else:
        priority = None
    return priority
