import json
from os import environ

from flask_cors import CORS

from hyp3_api import STEP_FUNCTION_CLIENT, connexion_app


def submit_job(body):
    parameters = body['parameters']
    job = STEP_FUNCTION_CLIENT.start_execution(
        stateMachineArn=environ['stateMachineArn'],
        input=json.dumps(parameters)
    )
    print(job)
    response = {
        'jobId': job['jobId'],
        'parameters': parameters,
    }

    return response


connexion_app.add_api('openapi-spec.yml')
CORS(connexion_app.app, origins=r'https?://([-\w]+\.)*asf\.alaska\.edu', supports_credentials=True)
