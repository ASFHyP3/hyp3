import json
from os import getenv

import boto3

client: boto3 = boto3.client('batch')


def lambda_handler(event, context):
    parameters = json.loads(event['body'])
    job = client.submit_job(jobName=parameters['granule'],
                      jobQueue=getenv('JobQueue'),
                      jobDefinition=getenv('JobDefinition'),
                      parameters={
                          'granule': parameters['granule']
                      }
                      )

    response = {
        'Job Name': job['jobName'],
        'Job Id': job['jobId']

    }
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }