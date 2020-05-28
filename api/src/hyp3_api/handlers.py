from os import environ

from flask_cors import CORS
from hyp3_api import BATCH_CLIENT, connexion_app


def submit_job(body):
    job = BATCH_CLIENT.submit_job(
        jobName=body['granule'],
        jobQueue=environ['JOB_QUEUE'],
        jobDefinition=environ['JOB_DEFINITION'],
        parameters=body
    )
    response = {
        'jobId': job['jobId'],
        'parameters': body,
    }
    return response


connexion_app.add_api('openapi-spec.yml')
CORS(connexion_app.app, origins=r'https?://([-\w]+\.)*asf\.alaska\.edu', supports_credentials=True)
