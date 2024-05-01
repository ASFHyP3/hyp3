import os
from datetime import datetime, timezone
from decimal import Decimal
from os import environ

import botocore.exceptions

from dynamo.util import DYNAMODB_RESOURCE

APPLICATION_NOT_STARTED = 'NOT STARTED'
APPLICATION_PENDING = 'PENDING'
APPLICATION_APPROVED = 'APPROVED'
APPLICATION_REJECTED = 'REJECTED'


class DatabaseConditionException(Exception):
    """Raised when a DynamoDB condition expression check fails."""

# TODO: should the following two exception types just be based on the HTTP error code that should be raised,
#  e.g. 403Error?


class UnapprovedUserError(Exception):
    """Raised when the user is not approved for processing."""


class CannotUpdateUserError(Exception):
    """Raised when the user record cannot be updated."""


def update_user(user_id: str, body: dict) -> dict:
    # TODO also set derived EDL fields
    user = get_or_create_user(user_id)
    application_status = user['application_status']
    if application_status in (APPLICATION_NOT_STARTED, APPLICATION_PENDING):
        users_table = DYNAMODB_RESOURCE.Table(environ['USERS_TABLE_NAME'])
        try:
            users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='SET use_case = :use_case, application_status = :pending',
                ConditionExpression='application_status IN (:not_started, :pending)',
                ExpressionAttributeValues={
                    ':use_case': body['use_case'],
                    ':not_started': APPLICATION_NOT_STARTED,
                    ':pending': APPLICATION_PENDING
                },
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise DatabaseConditionException(f'Failed to update record for user {user_id}')
            raise
    elif application_status == APPLICATION_REJECTED:
        raise CannotUpdateUserError(
            f'Unfortunately, the application for user {user_id} has been rejected.'
            ' If you believe this was a mistake, please email ASF User Services at: uso@asf.alaska.edu'
        )
    elif application_status == APPLICATION_APPROVED:
        raise CannotUpdateUserError(f'The application for user {user_id} has already been approved.')
    else:
        raise ValueError(f'User {user_id} has an invalid application status: {application_status}')
    # TODO return updated user record
    return {}


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
            users_table=users_table,
        )
    return user


def _get_current_month() -> str:
    return datetime.now(tz=timezone.utc).strftime('%Y-%m')


def _create_user(user_id: str, users_table) -> dict:
    # TODO rename month_of_last_credits_reset -> month_of_last_credit_reset
    user = {
        'user_id': user_id,
        'remaining_credits': Decimal(0),
        'month_of_last_credits_reset': '0',
        'application_status': APPLICATION_NOT_STARTED
    }
    try:
        users_table.put_item(Item=user, ConditionExpression='attribute_not_exists(user_id)')
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise DatabaseConditionException(f'Failed to create user {user_id}')
        raise
    return user


def _reset_credits_if_needed(user: dict, default_credits: Decimal, current_month: str, users_table) -> dict:
    if (
            os.environ['RESET_CREDITS_MONTHLY'] == 'true'
            and user['application_status'] == APPLICATION_APPROVED
            and user['month_of_last_credits_reset'] < current_month  # noqa: W503
            and user['remaining_credits'] is not None  # noqa: W503
    ):
        user['month_of_last_credits_reset'] = current_month
        user['remaining_credits'] = user.get('credits_per_month', default_credits)
        try:
            users_table.put_item(
                Item=user,
                ConditionExpression=(
                    'application_status = :approved'
                    ' AND month_of_last_credits_reset < :current_month'
                    ' AND attribute_type(remaining_credits, :number)'
                ),
                ExpressionAttributeValues={
                    ':approved': APPLICATION_APPROVED,
                    ':current_month': current_month,
                    ':number': 'N',
                },
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise DatabaseConditionException(
                    f'Failed to perform monthly credit reset for approved user {user["user_id"]}'
                )
            raise
    elif user['application_status'] != APPLICATION_APPROVED:
        # TODO should we also check RESET_CREDITS_MONTHLY for this case? should we perhaps get rid of that
        #  variable for now since hyp3-enterprise-test is the only deployment that sets it false?
        user['month_of_last_credits_reset'] = '0'
        user['remaining_credits'] = Decimal(0)
        try:
            users_table.put_item(
                Item=user,
                ConditionExpression='NOT (application_status = :approved)',
                ExpressionAttributeValues={':approved': APPLICATION_APPROVED},
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise DatabaseConditionException(
                    f'Failed to perform monthly credit reset for unapproved user {user["user_id"]}'
                )
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
