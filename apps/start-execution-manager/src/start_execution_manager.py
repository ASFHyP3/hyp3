import json
import logging
import os
import sys

import boto3

import dynamo

LAMBDA_CLIENT = boto3.client('lambda')

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handle_exception(exc_type, value, traceback) -> None:
    logger.critical('Unhandled exception', exc_info=(exc_type, value, traceback))


sys.excepthook = handle_exception


def invoke_worker(worker_function_arn: str, jobs: list[dict]) -> dict:
    payload = json.dumps(
        {'jobs': dynamo.util.convert_decimals_to_numbers(jobs)}
    )
    return LAMBDA_CLIENT.invoke(
        FunctionName=worker_function_arn,
        InvocationType='Event',
        Payload=payload,
    )


def lambda_handler(event, context) -> None:
    worker_function_arn = os.environ['START_EXECUTION_WORKER_ARN']
    logger.info(f'Worker function ARN: {worker_function_arn}')

    pending_jobs = dynamo.jobs.get_jobs_waiting_for_execution(limit=900)
    logger.info(f'Got {len(pending_jobs)} pending jobs')

    batch_size = 300
    for i in range(0, len(pending_jobs), batch_size):
        jobs = pending_jobs[i:i + batch_size]
        logger.info(f'Invoking worker for {len(jobs)} jobs')
        response = invoke_worker(worker_function_arn, jobs)
        logger.info(f'Got response status code {response["StatusCode"]}')
