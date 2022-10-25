import json
import logging
import os
import sys
from typing import Any

import boto3

STEP_FUNCTION = boto3.client('stepfunctions')

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handle_exception(exc_type, value, traceback) -> None:
    logger.critical('Unhandled exception', exc_info=(exc_type, value, traceback))


sys.excepthook = handle_exception


def convert_to_string(obj: Any) -> str:
    if isinstance(obj, list):
        return ' '.join([str(item) for item in obj])
    return str(obj)


def convert_parameters_to_strings(parameters: dict[str, Any]) -> dict[str, str]:
    return {key: convert_to_string(value) for key, value in parameters.items()}


def submit_jobs(jobs: list[dict]) -> None:
    step_function_arn = os.environ['STEP_FUNCTION_ARN']
    logger.info(f'Step function ARN: {step_function_arn}')
    for job in jobs:
        # Convert parameters to strings so they can be passed to Batch; see:
        # https://docs.aws.amazon.com/batch/latest/APIReference/API_SubmitJob.html#Batch-SubmitJob-request-parameters
        job['job_parameters'] = convert_parameters_to_strings(job['job_parameters'])
        STEP_FUNCTION.start_execution(
            stateMachineArn=step_function_arn,
            input=json.dumps(job, sort_keys=True),
            name=job['job_id'],
        )


def lambda_handler(event, context) -> None:
    jobs = event['jobs']
    logger.info(f'Submitting {len(jobs)} jobs')
    submit_jobs(jobs)
    logger.info('Successfully submitted jobs')
