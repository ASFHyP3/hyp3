from os import environ

from dynamo.util import DYNAMODB_RESOURCE


def get_user(user):
    table = DYNAMODB_RESOURCE.Table(environ['USERS_TABLE_NAME'])
    response = table.get_item(Key={'user_id': user})
    return response.get('Item')


def get_max_jobs_per_month(user):
    user = get_user(user)
    if user:
        max_jobs_per_month = user['max_jobs_per_month']
    else:
        max_jobs_per_month = int(environ['MONTHLY_JOB_QUOTA_PER_USER'])
    return max_jobs_per_month
