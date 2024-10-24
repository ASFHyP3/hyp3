import json
from os import environ

import boto3
from botocore.config import Config

config = Config(retries={'max_attempts': 2, 'mode': 'standard'})
CLOUDWATCH = boto3.client('logs', config=config)
S3 = boto3.client('s3')


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


def write_log_to_s3(bucket, prefix, name, content, content_type: str = 'text/plain'):
    key = f'{prefix}/{name}'
    S3.put_object(Bucket=bucket, Key=key, Body=content, ContentType=content_type)
    tag_set = {
        'TagSet': [
            {
                'Key': 'file_type',
                'Value': 'log',
            },
        ],
    }
    S3.put_object_tagging(Bucket=bucket, Key=key, Tagging=tag_set)


def get_last_log_event(log_stream):
    try:
        response = CLOUDWATCH.describe_log_streams(logGroupName='/aws/batch/job', logStreamNamePrefix=log_stream)
        last_event_time = response['logStreams'][0]['lastEventTimestamp']

        log_query = {
            'logGroupName': '/aws/batch/job',
            'logStreamName': log_stream,
            'startTime': last_event_time - 1_000,  # milliseconds since 1970-01-01T00:00:00Z
            'endTime': last_event_time  + 1_000,  # milliseconds since 1970-01-01T00:00:00Z
        }
        response = CLOUDWATCH.get_log_events(**log_query)
        return response['events'][-1]['message']
    except:
        return None


def lambda_handler(event, context):
    bucket = environ['BUCKET']
    prefix = event['prefix']

    _, last_result = max(event['processing_results'].items(), key=lambda x: x[0])
    assert 'Error' in last_result

    cause = json.loads(last_result['Cause'])

    for attempt in cause['Attempts']:
        log_stream = attempt['Container'].get('LogStreamName')
        if log_stream:
            attempt['LastLogEvent'] = get_last_log_event(log_stream)
        else:
            attempt['LastLogEvent'] = None

    write_log_to_s3(bucket, prefix, f'{prefix}.json', json.dumps(cause), content_type='application/json')

    last_log_content = None

    last_log_stream = cause['Attempts'][-1].get('LogStreamName')
    if last_log_stream:
        try:
            last_log_content = get_log_content(event['log_group'], last_log_stream)
        except CLOUDWATCH.exceptions.ResourceNotFoundException as e:
            if 'specified log stream does not exist' not in str(e):
                raise

    if last_log_content:
        write_log_to_s3(bucket, prefix, f'{prefix}.log', last_log_content)
