import json
import os

import boto3

STEP_FUNCTION = boto3.client('stepfunctions')


def convert_to_string(obj):
    if isinstance(obj, list):
        return ' '.join([str(item) for item in obj])
    return str(obj)


def convert_parameters_to_strings(parameters):
    return {key: convert_to_string(value) for key, value in parameters.items()}


def submit_jobs(jobs):
    step_function_arn = os.environ['STEP_FUNCTION_ARN']
    for job in jobs:
        # Convert parameters to strings so they can be passed to Batch; see:
        # https://docs.aws.amazon.com/batch/latest/APIReference/API_SubmitJob.html#Batch-SubmitJob-request-parameters
        job['job_parameters'] = convert_parameters_to_strings(job['job_parameters'])
        STEP_FUNCTION.start_execution(
            stateMachineArn=step_function_arn,
            input=json.dumps(job, sort_keys=True),
            name=job['job_id'],
        )


# TODO add logging
# TODO add type hints
def lambda_handler(event, context):
    submit_jobs(event['jobs'])
