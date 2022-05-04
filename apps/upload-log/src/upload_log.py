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


def get_log_content_from_failed_attempts(cause: dict) -> str:
    status = cause['Status']
    status_reason = cause['StatusReason']

    assert status == 'FAILED', status
    assert status_reason == 'Task failed to start', status_reason

    return '\n'.join(attempt['Container']['Reason'] for attempt in cause['Attempts'])


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


def lambda_handler(event, context):
    log_stream = get_log_stream(event['processing_results'])
    try:
        log_content = get_log_content(event['log_group'], log_stream)
    except CLOUDWATCH.exceptions.ResourceNotFoundException as e:
        if 'specified log stream does not exist' in str(e):
            assert 'Error' in event['processing_results']
            log_content = get_log_content_from_failed_attempts(json.loads(event['processing_results']['Cause']))
        else:
            raise
    write_log_to_s3(environ['BUCKET'], event['prefix'], log_content)
