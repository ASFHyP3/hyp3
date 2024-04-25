import os
from datetime import datetime, timezone
from decimal import Decimal
from os import environ

import botocore.exceptions

from dynamo.util import DYNAMODB_RESOURCE

APPLICATION_APPROVED = 'APPROVED'
APPLICATION_PENDING = 'PENDING'
APPLICATION_REJECTED = 'REJECTED'


class DatabaseConditionException(Exception):
    """Raised when a DynamoDB condition expression check fails."""


class UnapprovedUserError(Exception):
    """Raised when the user is not approved for processing."""


def get_user(user_id: str) -> dict:
    current_month = _get_current_month()
    default_credits = Decimal(os.environ['DEFAULT_CREDITS_PER_USER'])

    users_table = DYNAMODB_RESOURCE.Table(environ['USERS_TABLE_NAME'])
    user = users_table.get_item(Key={'user_id': user_id}).get('Item')

    if user is None:
        raise UnapprovedUserError(
            # TODO: replace <url> with registration form URL
            f'User {user_id} has not yet applied for a monthly credit allotment.'
            ' Please visit <url> to submit your application.'
        )

    return _reset_credits_if_needed(
        user=user,
        default_credits=default_credits,
        current_month=current_month,
        users_table=users_table,
    )


def _get_current_month() -> str:
    return datetime.now(tz=timezone.utc).strftime('%Y-%m')


# TODO: call this function for the user registration endpoint
def create_user(user_id: str, users_table) -> dict:
    user = {'user_id': user_id, 'remaining_credits': Decimal(0), 'month_of_last_credits_reset': '0'}
    try:
        users_table.put_item(Item=user, ConditionExpression='attribute_not_exists(user_id)')
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # TODO: replace this with a different exception and convert it to a client error
            #  for the user registration endpoint
            raise DatabaseConditionException(f'Failed to create user {user_id}')
        raise
    return user


def _reset_credits_if_needed(user: dict, default_credits: Decimal, current_month: str, users_table) -> dict:
    # TODO:
    #  if application_status is APPROVED:
    #    take the current approach
    #  elif application_status is PENDING or REJECTED:
    #    set remaining_credits and month of last reset to 0 (like in create_user)
    if (
            os.environ['RESET_CREDITS_MONTHLY'] == 'true'
            and user['month_of_last_credits_reset'] < current_month  # noqa: W503
            and user['remaining_credits'] is not None  # noqa: W503
    ):
        user['month_of_last_credits_reset'] = current_month
        user['remaining_credits'] = user.get('credits_per_month', default_credits)
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


def decrement_credits(user_id: str, cost: Decimal) -> None:
    if cost <= Decimal(0):
        raise ValueError(f'Cost {cost} <= 0')
    users_table = DYNAMODB_RESOURCE.Table(environ['USERS_TABLE_NAME'])
    try:
        users_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='ADD remaining_credits :delta',
            ConditionExpression='remaining_credits >= :cost',
            ExpressionAttributeValues={':cost': cost, ':delta': -cost},
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise DatabaseConditionException(f'Failed to decrement credits for user {user_id}')
        raise
