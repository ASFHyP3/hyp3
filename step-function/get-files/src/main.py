from datetime import datetime
from os import environ
from os.path import basename

import boto3

S3_CLIENT = boto3.client('s3')
BUCKET = environ['BUCKET']

def get_download_url(key):
    bucket = environ['BUCKET']
    region = environ['AWS_REGION']
    return f'https://{bucket}.s3.{region}.amazonaws.com/{key}'


def get_expiration_time(key):
    s3_object = S3_CLIENT.get_object(Bucket=BUCKET, Key=key)
    expiration_string = s3_object['Expiration'].split('"')[1]
    expiration_datetime = datetime.strptime(expiration_string, '%a, %d %b %Y %H:%M:%S %Z')
    return expiration_datetime.isoformat(timespec='seconds') + '+00:00'


def get_object_file_type(key):
    response = S3_CLIENT.get_object_tagging(Bucket=BUCKET, Key=key)
    for tag in response['TagSet']:
        if tag['Key'] == 'file_type':
            return tag['Value']
    return None


def lambda_handler(event, context):
    response = S3_CLIENT.list_objects_v2(Bucket=BUCKET, Prefix=event['job_id'])

    files = []
    browse_images = []
    thumbnail_images = []

    for item in response['Contents']:
        download_url = get_download_url(item['Key'])
        file_type = get_object_file_type(item['Key'])
        if file_type == 'browse':
            browse_images.append(download_url)
        elif file_type == 'thumbnail':
            thumbnail_images.append(download_url)
        else:
            file = {
                'url': download_url,
                'size': item['Size'],
                'filename': basename(item['Key']),
            }
            files.append(file)

    return {
        'expiration_time': get_expiration_time(response['Contents'][0]['Key']),
        'files': files,
        'browse_images': browse_images,
        'thumbnail_images': thumbnail_images,
    }
