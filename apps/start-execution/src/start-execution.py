import json
import os

import boto3

import dynamo
from lambda_logging import log_exceptions, logger

LAMBDA_CLIENT = boto3.client('lambda')

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
    # Convert parameters to strings so they can be passed to Batch; see:
    # https://docs.aws.amazon.com/batch/latest/APIReference/API_SubmitJob.html#Batch-SubmitJob-request-parameters
    return {
        key: convert_to_string(value)
        for key, value in job['job_parameters'].items()
        if key in BATCH_PARAMS_BY_JOB_TYPE[job['job_type']]
    }


def submit_jobs(jobs: list[dict]) -> None:
    step_function_arn = os.environ['STEP_FUNCTION_ARN']
    logger.info(f'Step function ARN: {step_function_arn}')
    for job in jobs:
        job['batch_job_parameters'] = get_batch_job_parameters(job)
        STEP_FUNCTION.start_execution(
            stateMachineArn=step_function_arn,
            input=json.dumps(job, sort_keys=True),
            name=job['job_id'],
        )


def invoke_worker(worker_function_arn: str, jobs: list[dict]) -> dict:
    payload = json.dumps({'jobs': dynamo.util.convert_decimals_to_numbers(jobs)})
    return LAMBDA_CLIENT.invoke(
        FunctionName=worker_function_arn,
        InvocationType='Event',
        Payload=payload,
    )


@log_exceptions
def lambda_handler(event: dict, _) -> None:
    worker_function_arn = os.environ['START_EXECUTION_WORKER_ARN']
    logger.info(f'Worker function ARN: {worker_function_arn}')

    pending_jobs = dynamo.jobs.get_jobs_waiting_for_execution(limit=500)
    logger.info(f'Got {len(pending_jobs)} pending jobs')

    batch_size = 250
    for i in range(0, len(pending_jobs), batch_size):
        jobs = pending_jobs[i : i + batch_size]
        logger.info(f'Invoking worker for {len(jobs)} jobs')
        submit_jobs(jobs)

