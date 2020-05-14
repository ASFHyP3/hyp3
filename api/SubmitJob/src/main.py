import json
from os import environ

import boto3

client = boto3.client('batch')


def lambda_handler(event, context):
    parameters = json.loads(event['body'])
    job = client.submit_job(jobQueue=environ['JOB_QUEUE'],
                            jobDefinition=environ['JOB_NAME'],
                            parameters=parameters
                            )
    response = {
        'jobName': job['jobName'],
        'jobId': job['jobId']

    }
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
