from os import environ

from flask_cors import CORS
from hyp3_api import BATCH_CLIENT, connexion_app


def submit_job(body):
    parameters = body['parameters']
    print(parameters)
    job = BATCH_CLIENT.submit_job(
        jobName=parameters['granule'],
        jobQueue=environ['JOB_QUEUE'],
        jobDefinition=environ['JOB_DEFINITION'],
        parameters=parameters
    )
    print(job)
    response = {
        'jobId': job['jobId'],
        'parameters': parameters,
    }

    return response


connexion_app.add_api('openapi-spec.yml')
CORS(connexion_app.app, origins=r'https?://([-\w]+\.)*asf\.alaska\.edu', supports_credentials=True)
