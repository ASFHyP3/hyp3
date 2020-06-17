import decimal
import json
from os import environ

import boto3
from boto3.dynamodb.conditions import Attr

DB = boto3.resource('dynamodb')
STEP_FUNCTION = boto3.client('stepfunctions')


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return int(o)
        return super(DecimalEncoder, self).default(o)


def lambda_handler(event, context):
    table = DB.Table(environ['TABLE_NAME'])
    filter_expression = Attr('status_code').eq('PENDING')
    response = table.scan(FilterExpression=filter_expression)
    pending_jobs = response['Items']

    for job in pending_jobs:
        STEP_FUNCTION.start_execution(
            stateMachineArn=environ['STEP_FUNCTION_ARN'],
            input=json.dumps(job),
            name=job['job_id']
        )
