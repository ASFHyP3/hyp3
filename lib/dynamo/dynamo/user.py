import os
from decimal import Decimal
from os import environ
from typing import Optional

import botocore.exceptions
from dynamo.util import DYNAMODB_RESOURCE


def get_user(user_id: str) -> Optional[dict]:
    table = DYNAMODB_RESOURCE.Table(environ['USERS_TABLE_NAME'])
    response = table.get_item(Key={'user_id': user_id})
    return response.get('Item')


def create_user(user_id: str) -> dict:
    table = DYNAMODB_RESOURCE.Table(environ['USERS_TABLE_NAME'])
    if get_user(user_id):
        raise ValueError(f'user {user_id} already exists')
    user = {'user_id': user_id, 'remaining_credits': Decimal(os.environ['DEFAULT_CREDITS_PER_USER'])}
    table.put_item(Item=user)
    return user


# TODO unit tests
def decrement_credits(user_id: str, cost: float) -> None:
    if cost < 0:
        raise ValueError(f'Cost {cost} < 0')
    table = DYNAMODB_RESOURCE.Table(environ['USERS_TABLE_NAME'])
    try:
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='ADD remaining_credits :delta',
            ConditionExpression='remaining_credits >= :cost',
            ExpressionAttributeValues={':cost': Decimal(cost), ':delta': Decimal(-cost)},
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # TODO provide better error message accounting for case where user_id does not exist in the table
            raise ValueError(
                f'Subtracting cost {cost} from user\'s remaining credits would result in a negative balance'
            )
        raise
