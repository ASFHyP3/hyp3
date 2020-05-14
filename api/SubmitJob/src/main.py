import json
from os import environ

import boto3

client = boto3.client('batch')


def lambda_handler(event, context):
    parameters = json.loads(event['body'])
    job = client.submit_job(jobName=parameters['granule'],
                            jobQueue=environ['JobQueue'],
                            jobDefinition=environ['JobDefinition'],
                            parameters=parameters
                            )
    response = {
        'Job Name': job['jobName'],
        'Job Id': job['jobId']

    }
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
