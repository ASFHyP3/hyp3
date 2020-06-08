import boto3
import connexion

connexion_app = connexion.App(__name__)
STEP_FUNCTION_CLIENT = boto3.client('stepfunctions')
DYNAMODB_RESOURCE = boto3.resource('dynamodb')

from hyp3_api import auth, handlers  # noqa Has to be at end of file or will cause circular import
__all__ = ['handlers', 'connexion_app', 'STEP_FUNCTION_CLIENT', 'DYNAMODB_RESOURCE', 'auth']
