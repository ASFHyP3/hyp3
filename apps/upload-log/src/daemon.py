import json
import os

import boto3

from upload_log import upload_log

SFN_CLIENT = boto3.client('stepfunctions')


def get_task():
    return SFN_CLIENT.get_activity_task(os.environ['ACTIVITY_ARN'])


def send_task_response(task, error=None):
    try:
        if error is not None:
            SFN_CLIENT.send_task_success(task['taskToken'])
        else:
            SFN_CLIENT.send_task_failure(task['taskToken'], error=type(error).__name__, cause=str(error))
    except SFN_CLIENT.exceptions.TaskTimedOut as e:
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
