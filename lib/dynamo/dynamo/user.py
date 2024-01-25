import os
from datetime import datetime, timezone
from decimal import Decimal
from os import environ

import botocore.exceptions

from dynamo.util import DYNAMODB_RESOURCE


class DatabaseConditionException(Exception):
    """Raised when a DynamoDB condition expression check fails."""


def get_or_create_user(user_id: str) -> dict:
    current_month = _get_current_month()
    default_credits = Decimal(os.environ['DEFAULT_CREDITS_PER_USER'])

    users_table = DYNAMODB_RESOURCE.Table(environ['USERS_TABLE_NAME'])
    user = users_table.get_item(Key={'user_id': user_id}).get('Item')

    if user is not None:
        user = _reset_credits_if_needed(
            user=user,
            default_credits=default_credits,
            current_month=current_month,
            users_table=users_table,
        )
    else:
        user = _create_user(
            user_id=user_id,
            default_credits=default_credits,
            current_month=current_month,
            users_table=users_table,
        )
    return user


def _get_current_month() -> str:
    return datetime.now(tz=timezone.utc).strftime('%Y-%m')


def _create_user(user_id: str, default_credits: Decimal, current_month: str, users_table) -> dict:
    user = {'user_id': user_id, 'remaining_credits': default_credits, 'month_of_last_credits_reset': current_month}
    try:
        users_table.put_item(Item=user, ConditionExpression='attribute_not_exists(user_id)')
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise DatabaseConditionException(f'Failed to create user {user_id}')
        raise
    return user


# TODO tests
def _reset_credits_if_needed(user: dict, default_credits: Decimal, current_month: str, users_table) -> dict:
    if (
            os.environ['RESET_CREDITS_MONTHLY'] == 'yes'
            and user['month_of_last_credits_reset'] < current_month
            and user['remaining_credits'] is not None
    ):
        user['month_of_last_credits_reset'] = current_month
        user['remaining_credits'] = default_credits
        try:
            users_table.put_item(
                Item=user,
                ConditionExpression='month_of_last_credits_reset < :current_month'
                                    ' AND attribute_type(remaining_credits, :number)',
                ExpressionAttributeValues={
                    ':current_month': current_month,
                    ':number': 'N',
                },
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise DatabaseConditionException(f'Failed to perform monthly credits reset for user {user["user_id"]}')
            raise
    return user


# TODO tests
def decrement_credits(user_id: str, cost: float) -> None:
    if cost <= 0:
        raise ValueError(f'Cost {cost} <= 0')
    users_table = DYNAMODB_RESOURCE.Table(environ['USERS_TABLE_NAME'])
    try:
        users_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='ADD remaining_credits :delta',
            ConditionExpression='remaining_credits >= :cost',
            ExpressionAttributeValues={':cost': Decimal(cost), ':delta': Decimal(-cost)},
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise DatabaseConditionException(f'Failed to decrement credits for user {user_id}')
        raise
