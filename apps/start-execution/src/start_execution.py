import json
from decimal import Decimal
from os import environ

import boto3

from dynamo import jobs

STEP_FUNCTION = boto3.client('stepfunctions')


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if int(o) == o:
                return int(o)
            return float(o)
        return super(DecimalEncoder, self).default(o)


def convert_parameters_to_strings(parameters):
    parameters['granules'] = ' '.join(parameters['granules'])
    return {key: str(value) for key, value in parameters.items()}


def submit_jobs(jobs):
    for job in jobs:
        job['job_parameters'] = convert_parameters_to_strings(job['job_parameters'])
        STEP_FUNCTION.start_execution(
            stateMachineArn=environ['STEP_FUNCTION_ARN'],
            input=json.dumps(job, cls=DecimalEncoder, sort_keys=True),
            name=job['job_id'],
        )


def lambda_handler(event, context):
    pending_jobs = jobs.get_jobs_by_status_code('PENDING', limit=400)
    submit_jobs(pending_jobs)
