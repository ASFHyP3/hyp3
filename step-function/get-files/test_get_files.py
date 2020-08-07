from os import environ

import pytest
from botocore.stub import Stubber
from src.main import S3_CLIENT, get_expiration_time, get_object_file_type, lambda_handler


@pytest.fixture(autouse=True)
def setup_env():
    environ['BUCKET'] = 'mybucket'
    environ['AWS_REGION'] = 'region'


@pytest.fixture
def s3_stubber():
    with Stubber(S3_CLIENT) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


def stub_experation(s3_stubber: Stubber, key):
    params = {
        'Bucket': 'mybucket',
        'Key': key
    }
    s3_response = {
        'Expiration': 'expiry-date="Wed, 01 Jan 2020 00:00:00 UTC", '
                      'rule-id="MDQxMzRmZTgtNDFlMi00Y2UwLWIyZjEtMTEzYTllNDNjYjJk"'
    }
    s3_stubber.add_response(method='get_object', expected_params=params, service_response=s3_response)


def test_get_expiration(s3_stubber: Stubber):
    stub_experation(s3_stubber, 'mykey')
    response = get_expiration_time('mybucket', 'mykey')
    assert response == '2020-01-01T00:00:00+00:00'


def stub_file_type(s3_stubber: Stubber, key, file_type):
    params = {
        'Bucket': 'mybucket',
        'Key': key
    }
    s3_response = {
        'TagSet': [
            {
                'Key': 'file_type',
                'Value': file_type
            }
        ]
    }
    s3_stubber.add_response(method='get_object_tagging', expected_params=params, service_response=s3_response)


def test_get_file_type(s3_stubber: Stubber):
    stub_file_type(s3_stubber, 'mykey', 'product')
    response = get_object_file_type('mybucket', 'mykey')
    assert response == 'product'


def stub_list_files(s3_stubber: Stubber, files, job_id):
    params = {
        'Bucket': 'mybucket',
        'Prefix': job_id,
    }
    s3_response = {
        'Contents': [
            {
                'Key': job_id + item['key'],
                'Size': item['size']
            } for item in files
        ]
    }
    s3_stubber.add_response('list_objects_v2', expected_params=params, service_response=s3_response)


def test_get_files(s3_stubber: Stubber):
    files = [
        {
            'key': '/product',
            'size': 50,
        },
        {
            'key': '/thumbnail',
            'size': 5,
        },
        {
            'key': '/browse',
            'size': 10,
        },
    ]
    stub_list_files(s3_stubber, files, 'job_id')
    stub_file_type(s3_stubber, 'job_id/product', 'product')
    stub_experation(s3_stubber, 'job_id/product')
    stub_file_type(s3_stubber, 'job_id/thumbnail', 'thumbnail')
    stub_file_type(s3_stubber, 'job_id/browse', 'browse')

    event = {
        'job_id': 'job_id'
    }
    response = lambda_handler(event, None)
    assert response == {
        'expiration_time': '2020-01-01T00:00:00+00:00',
        'files': [
            {
                'url': 'https://mybucket.s3.region.amazonaws.com/job_id/product',
                'size': 50,
                'filename': 'product',
            }
        ],
        'browse_images': ['https://mybucket.s3.region.amazonaws.com/job_id/browse'],
        'thumbnail_images': ['https://mybucket.s3.region.amazonaws.com/job_id/thumbnail'],
    }
