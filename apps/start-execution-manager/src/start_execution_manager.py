import json
from decimal import Decimal
from os import environ

import boto3

from dynamo import jobs

STEP_FUNCTION = boto3.client('stepfunctions')

# TODO update


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if int(o) == o:
                return int(o)
            return float(o)
        return super(DecimalEncoder, self).default(o)


def convert_to_string(obj):
    if isinstance(obj, list):
        return ' '.join([str(item) for item in obj])
    return str(obj)


def convert_parameters_to_strings(parameters):
    return {key: convert_to_string(value) for key, value in parameters.items()}


def submit_jobs(jobs):
    for job in jobs:
        job['job_parameters'] = convert_parameters_to_strings(job['job_parameters'])
        STEP_FUNCTION.start_execution(
            stateMachineArn=environ['STEP_FUNCTION_ARN'],
            input=json.dumps(job, cls=DecimalEncoder, sort_keys=True),
            name=job['job_id'],
        )


def lambda_handler(event, context):
    pending_jobs = jobs.get_jobs_waiting_for_execution(limit=400)
    submit_jobs(pending_jobs)
