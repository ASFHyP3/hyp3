import json
import os
import urllib.parse
from datetime import datetime
from os import environ
from pathlib import Path
from typing import TypedDict

import boto3
import pystac

import dynamo


S3_CLIENT = boto3.client('s3')


class S3Location(TypedDict):
    bucket: str
    key: str


class S3Object(TypedDict):
    Key: str
    Size: int


class ProductFile(TypedDict):
    url: str
    size: int
    filename: str
    s3: S3Location


class S3File(TypedDict):
    download_url: str
    file_type: str
    size: int
    filename: str
    s3: S3Location


class StacFiles(TypedDict):
    files: list[ProductFile]
    browse_images: list[str]
    thumbnail_images: list[str]


class OrganizedFiles(TypedDict):
    files: list[ProductFile]
    browse_images: list[str]
    thumbnail_images: list[str]
    logs: list[str]
    expiration_time: str | None


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


def get_products(files: list[S3File]) -> list[ProductFile]:
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


def get_file_urls_by_type(file_list: list[S3File], file_type: str) -> list[str]:
    files = [item for item in file_list if file_type in item['file_type']]
    sorted_files = sorted(files, key=lambda x: x['file_type'])
    urls = [item['download_url'] for item in sorted_files]
    return urls


def is_stac_json(s3_object: S3Object) -> bool:
    return s3_object['Key'].endswith('.stac.json')


def organize_files_tags(s3_objects: list[S3Object], bucket: str) -> OrganizedFiles:
    all_files: list[S3File] = []
    expiration = None

    for item in s3_objects:
        download_url = get_download_url(bucket, item['Key'])
        file_type = get_object_file_type(bucket, item['Key'])
        assert file_type is not None, f"Can't find file type for {item}"

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


def get_s3_object_for(asset: pystac.Asset, s3_objects: list[S3Object]) -> S3Object:
    for s3_object in s3_objects:
        if s3_object['Key'].split('/')[-1] in asset.href:
            return s3_object

    assert False, f"Can't find s3_object for {asset}"


def organize_files_stac(s3_objects: list[S3Object], bucket: str) -> StacFiles:
    stac_s3_key = [obj['Key'] for obj in s3_objects if is_stac_json(obj)][0]

    stac_str = S3_CLIENT.get_object(Bucket=bucket, Key=stac_s3_key)['Body'].read()
    item = pystac.Item.from_dict(json.loads(stac_str))

    files: list[ProductFile] = []
    browse_images: list[str] = []
    thumbnail_images: list[str] = []

    for asset in item.get_assets().values():
        s3_object = get_s3_object_for(asset, s3_objects)
        key = s3_object['Key']
        url = get_download_url(bucket, key)

        if asset.roles is None:
            continue

        if 'overview' in asset.roles:
            browse_images.append(url)

        if 'thumbnail' in asset.roles:
            thumbnail_images.append(url)

        if 'data' not in asset.roles:
            continue

        files.append(
            {
                'url': url,
                'size': s3_object['Size'],
                'filename': Path(key).name,
                's3': {'bucket': bucket, 'key': key},
            }
        )

    return {
        'files': files,
        'browse_images': browse_images,
        'thumbnail_images': thumbnail_images,
    }


def organize_files(s3_objects: list[S3Object], bucket: str) -> OrganizedFiles:
    files = organize_files_tags(s3_objects, bucket)

    if any(is_stac_json(obj) for obj in s3_objects):
        stac_files = organize_files_stac(s3_objects, bucket)
        files = {
            'files': stac_files['files'],
            'browse_images': stac_files['browse_images'],
            'thumbnail_images': stac_files['thumbnail_images'],
            'logs': files['logs'],
            'expiration_time': files['expiration_time'],
        }

    return files


def lambda_handler(event: dict, context: object) -> None:
    response = S3_CLIENT.list_objects_v2(Bucket=event['bucket'], Prefix=event['bucket_prefix'])
    files = organize_files(response['Contents'], event['bucket'])
    dynamo.jobs.update_job({'job_id': event['job_id'], **files})
