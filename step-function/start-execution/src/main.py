from os import environ
import json

import boto3
from boto3.dynamodb.conditions import Attr

DB = boto3.resource('dynamodb')
STEP_FUNCTION = boto3.client('stepfunctions')


def lambda_handler(event, context):
    table = DB.Table('test-JobsTable-BUEBQNRB6FX3')
    filter_expression = Attr('status_code').eq('PENDING')
    response = table.scan(FilterExpression=filter_expression)
    pending_jobs = response['Items']

    for job in pending_jobs:
        STEP_FUNCTION.start_execution(
            stateMachineArn=environ['STEP_FUNCTION_ARN'],
            input=json.dumps(job, sort_keys=True),
        )