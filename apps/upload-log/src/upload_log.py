import json
from os import environ

import boto3

CLOUDWATCH = boto3.client('logs')
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
    key = f'{prefix}/log.txt'
    S3.put_object(Bucket=bucket, Key=key, Body=content, ContentType='text/plain')
    tag_set = {
        'TagSet': [
            {
                'Key': 'file_type',
                'Value': 'product',
            },
        ],
    }
    S3.put_object_tagging(Bucket=bucket, Key=key, Tagging=tag_set)


def lambda_handler(event, context):
    log_stream = get_log_stream(event['processing_results'])
    log_content = get_log_content(event['log_group'], log_stream)
    write_log_to_s3(environ['BUCKET'], event['prefix'], log_content)
