import boto3
from flask import Flask

app = Flask(__name__)
DYNAMODB_RESOURCE = boto3.resource('dynamodb')
CMR_URL = 'https://cmr.earthdata.nasa.gov/search/granules.json'

from hyp3_api import routes  # noqa Has to be at end of file or will cause circular import

__all__ = [
    'app',
    'DYNAMODB_RESOURCE',
    'CMR_URL',
    'routes',
]
