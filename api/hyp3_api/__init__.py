import boto3
from hyp3_api import definitions
import connexion

connexion_app = connexion.App(__name__)
BATCH_CLIENT = boto3.client('batch')
