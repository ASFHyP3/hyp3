import json
from decimal import Decimal
from os import environ

import boto3
from boto3.dynamodb.conditions import Attr

DB = boto3.resource('dynamodb')
STEP_FUNCTION = boto3.client('stepfunctions')


# support json serialization of Decimal values returned from dynamodb
def decimal_default(obj):
    if isinstance(obj, Decimal):
        if obj == int(obj):
            return int(obj)
        return float(obj)
    raise TypeError


def lambda_handler(event, context):
    table = DB.Table(environ['TABLE_NAME'])
    filter_expression = Attr('status_code').eq('PENDING')
    response = table.scan(FilterExpression=filter_expression)
    pending_jobs = response['Items']

    for job in pending_jobs:
        STEP_FUNCTION.start_execution(
            stateMachineArn=environ['STEP_FUNCTION_ARN'],
            input=json.dumps(job, default=decimal_default),
            name=job['job_id'],
        )
