from os import environ
from os.path import basename

import boto3

S3_CLIENT = boto3.client('s3')


def get_download_url(key):
    bucket = environ['BUCKET']
    region = environ['AWS_REGION']
    return f'https://{bucket}.s3.{region}.amazonaws.com/{key}'


def lambda_handler(event, context):
    response = S3_CLIENT.list_objects_v2(Bucket=environ['BUCKET'], Prefix=event['job_id'])
    return [
        {
            'url': get_download_url(item['Key']),
            'size': item['Size'],
            'filename': basename(item['Key']),
        }
        for item in response['Contents']
    ]
