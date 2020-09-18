import boto3
import connexion

connexion_app = connexion.App(__name__)
DYNAMODB_RESOURCE = boto3.resource('dynamodb')
CMR_URL = 'https://cmr.earthdata.nasa.gov/search/granules.json'

from hyp3_api import auth, handlers #noqa

__all__ = [
    'handlers',
    'connexion_app',
    'DYNAMODB_RESOURCE',
    'auth',
    'CMR_URL',
]
