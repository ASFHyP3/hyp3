import os
import urllib.parse
from datetime import datetime
from os import environ
from pathlib import Path

import boto3

import dynamo


S3_CLIENT = boto3.client('s3')


def get_download_url(bucket: str, key: str) -> str:
    if (bucket == environ['BUCKET']) and (distribution_url := os.getenv('DISTRIBUTION_URL')):
        return urllib.parse.urljoin(distribution_url, key)

    region = S3_CLIENT.head_bucket(Bucket=bucket)['BucketRegion']
    return f'https://{bucket}.s3.{region}.amazonaws.com/{key}'


def get_expiration_time(bucket: str, key: str) -> str:
    s3_object = S3_CLIENT.get_object(Bucket=bucket, Key=key)
    expiration = s3_object.get('Expiration')
    if expiration is None:
        # HyP3's 100th birthday; 100 years since first non-ASF job
        # https://hyp3-api.asf.alaska.edu/jobs/969ab836-aa95-4613-8673-2a0415949afa
        return '2120-10-21T00:00:00+00:00'

    expiration_string = s3_object['Expiration'].split('"')[1]
    expiration_datetime = datetime.strptime(expiration_string, '%a, %d %b %Y %H:%M:%S %Z')
    return expiration_datetime.isoformat(timespec='seconds') + '+00:00'


def get_object_file_type(bucket: str, key: str) -> str | None:
    response = S3_CLIENT.get_object_tagging(Bucket=bucket, Key=key)
    for tag in response['TagSet']:
        if tag['Key'] == 'file_type':
            return tag['Value']
    return None


def visible_product(product_path: str | Path) -> bool:
    return Path(product_path).suffix in ('.zip', '.nc', '.geojson', '.parquet')


def get_products(files: list[dict]) -> list[dict]:
    return [
        {
            'url': item['download_url'],
            'size': item['size'],
            'filename': item['filename'],
            's3': item['s3'],
        }
        for item in files
        if item['file_type'] == 'product' and visible_product(item['filename'])
    ]


def get_file_urls_by_type(file_list: list[dict], file_type: str) -> list[str]:
    files = [item for item in file_list if file_type in item['file_type']]
    sorted_files = sorted(files, key=lambda x: x['file_type'])
    urls = [item['download_url'] for item in sorted_files]
    return urls


def organize_files(s3_objects: list[dict], bucket: str) -> dict:
    all_files = []
    expiration = None
    for item in s3_objects:
        download_url = get_download_url(bucket, item['Key'])
        file_type = get_object_file_type(bucket, item['Key'])
        all_files.append(
            {
                'download_url': download_url,
                'file_type': file_type,
                'size': item['Size'],
                'filename': Path(item['Key']).name,
                's3': {
                    'bucket': bucket,
                    'key': item['Key'],
                },
            }
        )
        if expiration is None and file_type in ['product', 'log']:
            expiration = get_expiration_time(bucket, item['Key'])

    return {
        'files': get_products(all_files),
        'browse_images': get_file_urls_by_type(all_files, 'browse'),
        'thumbnail_images': get_file_urls_by_type(all_files, 'thumbnail'),
        'logs': get_file_urls_by_type(all_files, 'log'),
        'expiration_time': expiration,
    }


def lambda_handler(event: dict, context: object) -> None:
    response = S3_CLIENT.list_objects_v2(Bucket=event['bucket'], Prefix=event['bucket_prefix'])
    files = organize_files(response['Contents'], event['bucket'])
    dynamo.jobs.update_job({'job_id': event['job_id'], **files})
