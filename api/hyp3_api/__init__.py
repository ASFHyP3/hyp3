import boto3
import connexion

connexion_app = connexion.App(__name__)
BATCH_CLIENT = boto3.client('batch')

from hyp3_api import handlers, auth
__all__ = ['handlers', 'connexion_app', 'BATCH_CLIENT', 'auth']
