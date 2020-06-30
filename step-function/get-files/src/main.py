from datetime import datetime
from os import environ
from os.path import basename

import boto3

S3_CLIENT = boto3.client('s3')


def get_download_url(key):
    bucket = environ['BUCKET']
    region = environ['AWS_REGION']
    return f'https://{bucket}.s3.{region}.amazonaws.com/{key}'


def get_expiration_time(key):
    s3_object = S3_CLIENT.get_object(Bucket=environ['BUCKET'], Key=key)
    expiration_string = s3_object['Expiration'].split('"')[1]
    expiration_datetime = datetime.strptime(expiration_string, '%a, %d %b %Y %H:%M:%S %Z')
    return expiration_datetime.isoformat(timespec='seconds') + '+00:00'


def lambda_handler(event, context):
    response = S3_CLIENT.list_objects_v2(Bucket=environ['BUCKET'], Prefix=event['job_id'])
    return {
        'expiration_time': get_expiration_time(response['Contents'][0]['Key']),
        'files': [
            {
                'url': get_download_url(item['Key']),
                'size': item['Size'],
                'filename': basename(item['Key']),
            }
            for item in response['Contents']
        ],
    }
