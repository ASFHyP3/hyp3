import json
import os
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


SFN_CLIENT = boto3.client('stepfunctions')


def get_task():
    return SFN_CLIENT.get_activity_task(activityArn=os.environ['ACTIVITY_ARN'])


def send_task_response(task, error=None):
    try:
        if error is None:
            SFN_CLIENT.send_task_success(taskToken=task['taskToken'], output='{}')
        else:
            SFN_CLIENT.send_task_failure(taskToken=task['taskToken'], error=type(error).__name__, cause=str(error))
    except SFN_CLIENT.exceptions.TaskTimedOut:
        print('Failed to send response. Task timed out.')


def loop(get_remaining_time_in_millis):
    while get_remaining_time_in_millis() >= 15000:
        task = get_task()
        if 'taskToken' not in task:
            break
        try:
            task_input = json.loads(task['input'])
            upload_log(task_input)
            send_task_response(task)
        except Exception as e:  # noqa: let exception propigate to stepfunction by sending it in response
            send_task_response(task, error=e)


def lambda_handler(event, context):
    loop(context.get_remaining_time_in_millis)
