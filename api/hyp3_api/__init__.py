import boto3
import connexion

connexion_app = connexion.App(__name__)
application = connexion_app.app
BATCH_CLIENT = boto3.client('batch')

from hyp3_api import auth, handlers  # noqa Has to be at end of file or will cause circular import
__all__ = ['handlers', 'connexion_app', 'BATCH_CLIENT', 'auth']
