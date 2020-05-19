from os import environ
from hyp3_api import connexion_app, BATCH_CLIENT


def submit_job(body):
    job = BATCH_CLIENT.submit_job(
        jobName=body['granule'],
        jobQueue=environ['JOB_QUEUE'],
        jobDefinition=environ['JOB_DEFINITION'],
        parameters=body
    )
    response = {
        'jobId': job['jobId'],
        'jobName': job['jobName'],
        'parameters': body,
    }
    return response


connexion_app.add_api('spec.yml')