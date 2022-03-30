from datetime import datetime, timedelta, timezone
from os import environ
from uuid import uuid4

import dateutil.parser
from boto3.dynamodb.conditions import Attr, Key

from dynamo.util import DYNAMODB_RESOURCE, convert_floats_to_decimals, format_time


def validate_subscription(subscription):
    start = dateutil.parser.parse(subscription['search_parameters']['start'])
    end = dateutil.parser.parse(subscription['search_parameters']['end'])
    if end <= start:
        raise ValueError(f'End date: {format_time(end)} must be after start date: {format_time(start)}')

    end_threshold_in_days = 180
    max_end = datetime.now(tz=timezone.utc) + timedelta(days=end_threshold_in_days)
    if max_end <= end:
        raise ValueError(f'End date: {format_time(end)} must be within {end_threshold_in_days} days: '
                         f'{format_time(max_end)}')

    job_type = subscription.get('job_specification', {}).get('job_type')
    processing_level = subscription.get('search_parameters', {}).get('processingLevel', 'SLC')
    if job_type == 'INSAR_GAMMA' and processing_level != 'SLC':
        raise ValueError('processingLevel must be SLC when job_type is INSAR_GAMMA')


def put_subscription(user, subscription, validate_only=False):
    validate_subscription(subscription)

    defaults = {
        'subscription_id': str(uuid4()),
        'creation_date': format_time(datetime.now(tz=timezone.utc)),
        'user_id': user,
        'enabled': True,
    }
    for key, value in defaults.items():
        if key not in subscription:
            subscription[key] = value

    search_defaults = {
        'platform': 'S1',
        'processingLevel': 'SLC',
        'beamMode': ['IW'],
        'polarization': ['VV', 'VV+VH', 'HH', 'HH+HV'],
    }
    for key, value in search_defaults.items():
        if key not in subscription['search_parameters']:
            subscription['search_parameters'][key] = value

    table = DYNAMODB_RESOURCE.Table(environ['SUBSCRIPTIONS_TABLE_NAME'])
    if not validate_only:
        table.put_item(Item=convert_floats_to_decimals(subscription))
    return subscription


def get_subscriptions_for_user(user, name=None, job_type=None, enabled=None):
    table = DYNAMODB_RESOURCE.Table(environ['SUBSCRIPTIONS_TABLE_NAME'])

    filter_expression = Attr('subscription_id').exists()

    if name is not None:
        filter_expression &= Attr('job_specification.name').eq(name)
    if job_type is not None:
        filter_expression &= Attr('job_specification.job_type').eq(job_type)
    if enabled is not None:
        filter_expression &= Attr('enabled').eq(enabled)

    params = {
        'IndexName': 'user_id',
        'KeyConditionExpression': Key('user_id').eq(user),
        'FilterExpression': filter_expression,
        'ScanIndexForward': False
    }
    response = table.query(**params)
    subscriptions = response['Items']
    while 'LastEvaluatedKey' in response:
        params['ExclusiveStartKey'] = response['LastEvaluatedKey']
        response = table.query(**params)
        subscriptions.extend(response['Items'])
    return subscriptions


def get_subscription_by_id(subscription_id):
    table = DYNAMODB_RESOURCE.Table(environ['SUBSCRIPTIONS_TABLE_NAME'])
    response = table.get_item(Key={'subscription_id': subscription_id})
    return response.get('Item')


def get_all_subscriptions():
    table = DYNAMODB_RESOURCE.Table(environ['SUBSCRIPTIONS_TABLE_NAME'])

    response = table.scan()
    subscriptions = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        subscriptions.extend(response['Items'])
    return subscriptions
