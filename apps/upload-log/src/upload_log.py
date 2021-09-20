import json
from os import environ

import boto3
from botocore.config import Config

config = Config(retries={'max_attempts': 2, 'mode': 'standard'})
CLOUDWATCH = boto3.client('logs', config=config)
S3 = boto3.client('s3')


def get_log_stream(processing_results):
    if 'Error' in processing_results:
        processing_results = json.loads(processing_results['Cause'])
    return processing_results['Container']['LogStreamName']


def get_log_content(log_group, log_stream):
    response = CLOUDWATCH.get_log_events(logGroupName=log_group, logStreamName=log_stream, startFromHead=True)
    messages = [event['message'] for event in response['events']]

    next_token = None
    while response['nextForwardToken'] != next_token:
        next_token = response['nextForwardToken']
        response = CLOUDWATCH.get_log_events(logGroupName=log_group, logStreamName=log_stream, startFromHead=True,
                                             nextToken=next_token)
        messages.extend([event['message'] for event in response['events']])

    return '\n'.join(messages)


def write_log_to_s3(bucket, prefix, content):
    key = f'{prefix}/{prefix}.log'
    S3.put_object(Bucket=bucket, Key=key, Body=content, ContentType='text/plain')
    tag_set = {
        'TagSet': [
            {
                'Key': 'file_type',
                'Value': 'log',
            },
        ],
    }
    S3.put_object_tagging(Bucket=bucket, Key=key, Tagging=tag_set)


def upload_log(task_input):
    log_stream = get_log_stream(task_input['processing_results'])
    log_content = get_log_content(task_input['log_group'], log_stream)
    write_log_to_s3(environ['BUCKET'], task_input['prefix'], log_content)
