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
            # TODO condition fails if remaining_credits is null
            ConditionExpression='remaining_credits >= :cost',
            ExpressionAttributeValues={':cost': Decimal(cost), ':delta': Decimal(-cost)},
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise ValueError(
                f"Unable to update remaining_credits for user_id '{user_id}'."
                f' It is likely that the user record does not exist, remaining_credits < {cost},'
                ' or remaining_credits is of the wrong data type.'
            )
        raise
