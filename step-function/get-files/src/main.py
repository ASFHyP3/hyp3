from os import environ
from os.path import basename
from dateutil.parser import parse

import boto3

S3_CLIENT = boto3.client('s3')


def get_download_url(key):
    bucket = environ['BUCKET']
    region = environ['AWS_REGION']
    return f'https://{bucket}.s3.{region}.amazonaws.com/{key}'


def get_expiration(key):
    s3_object = S3_CLIENT.get_object(Bucket=environ['BUCKET'], Key=key)
    if 'Expiration' not in s3_object:
        return None
    expiration_string = s3_object['Expiration'].split('"')[1]
    return int(parse(expiration_string).timestamp())


def lambda_handler(event, context):
    response = S3_CLIENT.list_objects_v2(Bucket=environ['BUCKET'], Prefix=event['job_id'])
    return {
        'expiration_time': get_expiration(response['Contents'][0]['Key']),
        'files': [
            {
                'url': get_download_url(item['Key']),
                'size': item['Size'],
                'filename': basename(item['Key']),
            }
            for item in response['Contents']
        ],
    }
