from os import environ
from typing import Optional

from dynamo.util import DYNAMODB_RESOURCE


def get_user(user):
    table = DYNAMODB_RESOURCE.Table(environ['USERS_TABLE_NAME'])
    response = table.get_item(Key={'user_id': user})
    return response.get('Item')


def get_priority(user) -> Optional[int]:
    user = get_user(user)
    if user:
        priority = user.get('priority')
    else:
        priority = None
    return priority


def get_max_jobs_per_month(user) -> Optional[int]:
    user = get_user(user)
    if user:
        max_jobs_per_month = user['max_jobs_per_month']
        if max_jobs_per_month is not None:
            max_jobs_per_month = int(max_jobs_per_month)
    else:
        max_jobs_per_month = int(environ['MONTHLY_JOB_QUOTA_PER_USER'])
    return max_jobs_per_month
