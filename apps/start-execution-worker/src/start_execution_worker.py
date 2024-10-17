import json
import os
from pathlib import Path
from typing import Any

import boto3

from lambda_logging import log_exceptions, logger

STEP_FUNCTION = boto3.client('stepfunctions')

batch_params_file = Path(__file__).parent / 'batch_params_by_job_type.json'
if batch_params_file.exists():
    BATCH_PARAMS_BY_JOB_TYPE = json.loads(batch_params_file.read_text())
else:
    # Allows mocking with unittest.mock.patch
    BATCH_PARAMS_BY_JOB_TYPE = {}


def convert_to_string(obj: Any) -> str:
    if isinstance(obj, list):
        return ' '.join([str(item) for item in obj])
    return str(obj)


def get_batch_job_parameters(job: dict) -> dict[str, str]:
    return {
        key: convert_to_string(value)
        for key, value in job['job_parameters'].items()
        if key in BATCH_PARAMS_BY_JOB_TYPE[job['job_type']]
    }


def submit_jobs(jobs: list[dict]) -> None:
    step_function_arn = os.environ['STEP_FUNCTION_ARN']
    logger.info(f'Step function ARN: {step_function_arn}')
    for job in jobs:
        # Convert parameters to strings so they can be passed to Batch; see:
        # https://docs.aws.amazon.com/batch/latest/APIReference/API_SubmitJob.html#Batch-SubmitJob-request-parameters
        job['batch_job_parameters'] = get_batch_job_parameters(job)
        STEP_FUNCTION.start_execution(
            stateMachineArn=step_function_arn,
            input=json.dumps(job, sort_keys=True),
            name=job['job_id'],
        )


@log_exceptions
def lambda_handler(event, context) -> None:
    jobs = event['jobs']
    logger.info(f'Submitting {len(jobs)} jobs')
    submit_jobs(jobs)
    logger.info('Successfully submitted jobs')
