import json
import os

import boto3

import dynamo
from lambda_logging import log_exceptions, logger


LAMBDA_CLIENT = boto3.client('lambda')  # type: ignore[attr-defined]


def invoke_worker(worker_function_arn: str, jobs: list[dict]) -> dict:
    payload = json.dumps({'jobs': dynamo.util.convert_decimals_to_numbers(jobs)})
    return LAMBDA_CLIENT.invoke(
        FunctionName=worker_function_arn,
        InvocationType='Event',
        Payload=payload,
    )


@log_exceptions
def lambda_handler(event, context) -> None:
    worker_function_arn = os.environ['START_EXECUTION_WORKER_ARN']
    logger.info(f'Worker function ARN: {worker_function_arn}')

    pending_jobs = dynamo.jobs.get_jobs_waiting_for_execution(limit=500)
    logger.info(f'Got {len(pending_jobs)} pending jobs')

    batch_size = 250
    for i in range(0, len(pending_jobs), batch_size):
        jobs = pending_jobs[i : i + batch_size]
        logger.info(f'Invoking worker for {len(jobs)} jobs')
        response = invoke_worker(worker_function_arn, jobs)
        logger.info(f'Got response status code {response["StatusCode"]}')
