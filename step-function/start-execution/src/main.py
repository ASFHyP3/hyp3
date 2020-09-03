import json
from decimal import Decimal
from os import environ

import boto3
from boto3.dynamodb.conditions import Key

DB = boto3.resource('dynamodb')
STEP_FUNCTION = boto3.client('stepfunctions')


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if int(o) == o:
                return int(o)
            return float(o)
        return super(DecimalEncoder, self).default(o)


def get_pending_jobs():
    table = DB.Table(environ['TABLE_NAME'])
    response = table.query(
        IndexName='status_code',
        KeyConditionExpression=Key('status_code').eq('PENDING'),
    )
    return response['Items']


def convert_parameters_to_strings(parameters):
    for index, value in enumerate(parameters['granules']):
        parameters[f'granule{index}'] = value
    return {key: str(value) for key, value in parameters.items() if key != 'granules'}


def submit_jobs(jobs):
    for job in jobs:
        job['job_parameters'] = convert_parameters_to_strings(job['job_parameters'])
        STEP_FUNCTION.start_execution(
            stateMachineArn=environ['STEP_FUNCTION_ARN'],
            input=json.dumps(job, cls=DecimalEncoder, sort_keys=True),
            name=job['job_id']
        )


def lambda_handler(event, context):
    pending_jobs = get_pending_jobs()
    submit_jobs(pending_jobs)
