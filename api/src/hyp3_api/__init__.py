import boto3
import connexion

connexion_app = connexion.App(__name__)
DYNAMODB_RESOURCE = boto3.resource('dynamodb')

from hyp3_api import auth, handlers  # noqa Has to be at end of file or will cause circular import
__all__ = ['handlers', 'connexion_app', 'DYNAMODB_RESOURCE', 'auth']
