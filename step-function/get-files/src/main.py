from datetime import datetime
from os import environ
from os.path import basename

import boto3

S3_CLIENT = boto3.client('s3')


def get_download_url(bucket, key):
    region = environ['AWS_REGION']
    return f'https://{bucket}.s3.{region}.amazonaws.com/{key}'


def get_expiration_time(bucket, key):
    s3_object = S3_CLIENT.get_object(Bucket=bucket, Key=key)
    expiration_string = s3_object['Expiration'].split('"')[1]
    expiration_datetime = datetime.strptime(expiration_string, '%a, %d %b %Y %H:%M:%S %Z')
    return expiration_datetime.isoformat(timespec='seconds') + '+00:00'


def get_object_file_type(bucket, key):
    response = S3_CLIENT.get_object_tagging(Bucket=bucket, Key=key)
    for tag in response['TagSet']:
        if tag['Key'] == 'file_type':
            return tag['Value']
    return None


def lambda_handler(event, context):
    bucket = environ['BUCKET']
    response = S3_CLIENT.list_objects_v2(Bucket=bucket, Prefix=event['job_id'])

    files = []
    browse_images = []
    thumbnail_images = []
    expiration = None

    for item in response['Contents']:
        download_url = get_download_url(bucket, item['Key'])
        file_type = get_object_file_type(bucket, item['Key'])
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
            expiration = get_expiration_time(bucket, item['Key'])

    return {
        'expiration_time': expiration,
        'files': files,
        'browse_images': browse_images,
        'thumbnail_images': thumbnail_images,
    }
