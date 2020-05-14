import json
from os import environ

import boto3

BATCH_CLIENT = boto3.client('batch')


def lambda_handler(event, context):
    parameters = json.loads(event['body'])
    job = BATCH_CLIENT.submit_job(
        jobQueue=environ['JOB_QUEUE'],
        jobDefinition=environ['JOB_DEFINITION'],
        parameters=parameters
    )
    response = {
        'jobId': job['jobId']
    }
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
