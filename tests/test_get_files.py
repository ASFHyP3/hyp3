import os
from pathlib import Path
from unittest.mock import patch

import pytest
from botocore.stub import Stubber

import get_files


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv('BUCKET', 'myBucket')
    monkeypatch.setenv('AWS_REGION', 'myRegion')


@pytest.fixture
def s3_stubber():
    with Stubber(get_files.S3_CLIENT) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


def test_get_download_url(monkeypatch):
    assert os.getenv('DISTRIBUTION_URL') is None
    assert get_files.get_download_url('myBucket', 'myKey') == 'https://myBucket.s3.myRegion.amazonaws.com/myKey'

    monkeypatch.setenv('DISTRIBUTION_URL', '')
    assert get_files.get_download_url('myBucket', 'myKey') == 'https://myBucket.s3.myRegion.amazonaws.com/myKey'

    monkeypatch.setenv('DISTRIBUTION_URL', 'https://foo.com/')
    assert get_files.get_download_url('myBucket', 'myKey') == 'https://foo.com/myKey'

    monkeypatch.setenv('DISTRIBUTION_URL', 'https://foo.com')
    assert get_files.get_download_url('myBucket', 'myKey') == 'https://foo.com/myKey'


def stub_expiration(s3_stubber: Stubber, bucket, key):
    params = {'Bucket': bucket, 'Key': key}
    s3_response = {
        'Expiration': 'expiry-date="Wed, 01 Jan 2020 00:00:00 UTC", '
        'rule-id="MDQxMzRmZTgtNDFlMi00Y2UwLWIyZjEtMTEzYTllNDNjYjJk"'
    }
    s3_stubber.add_response(method='get_object', expected_params=params, service_response=s3_response)


def test_get_expiration(s3_stubber: Stubber):
    stub_expiration(s3_stubber, 'myBucket', 'myKey')
    response = get_files.get_expiration_time('myBucket', 'myKey')
    assert response == '2020-01-01T00:00:00+00:00'


def stub_get_object_tagging(s3_stubber: Stubber, bucket, key, file_type):
    params = {'Bucket': bucket, 'Key': key}
    s3_response = {'TagSet': [{'Key': 'file_type', 'Value': file_type}]}
    s3_stubber.add_response(method='get_object_tagging', expected_params=params, service_response=s3_response)


def test_get_file_type(s3_stubber: Stubber):
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myKey', file_type='product')
    response = get_files.get_object_file_type('myBucket', 'myKey')
    assert response == 'product'


def test_visible_product():
    assert not get_files.visible_product('myFile.tif')
    assert not get_files.visible_product('myFile.xml')
    assert not get_files.visible_product('myFile.md.txt')
    assert get_files.visible_product('myFile.zip')
    assert get_files.visible_product('myFile.nc')

    assert not get_files.visible_product(Path('myFile.tif'))
    assert not get_files.visible_product(Path('myFile.xml'))
    assert not get_files.visible_product(Path('myFile.md.txt'))
    assert get_files.visible_product(Path('myFile.zip'))
    assert get_files.visible_product(Path('myFile.nc'))


def stub_list_files(s3_stubber: Stubber, job_id, bucket, contents):
    params = {
        'Bucket': bucket,
        'Prefix': job_id,
    }
    s3_response = {
        'Contents': contents,
    }
    s3_stubber.add_response('list_objects_v2', expected_params=params, service_response=s3_response)


def test_get_files_zipped_product(s3_stubber: Stubber):
    files = [
        {
            'Key': 'myJobId/myProduct.zip',
            'Size': 50,
        },
        {
            'Key': 'myJobId/myProduct.tif',
            'Size': 30,
        },
        {
            'Key': 'myJobId/myThumbnail.png',
            'Size': 5,
        },
        {
            'Key': 'myJobId/myBrowse.png',
            'Size': 10,
        },
        {
            'Key': 'myJobId/myBrowse_rgb.png',
            'Size': 10,
        },
    ]
    stub_list_files(s3_stubber, 'myJobId', 'myBucket', files)
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myProduct.zip', 'product')
    stub_expiration(s3_stubber, 'myBucket', 'myJobId/myProduct.zip')
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myProduct.tif', 'product')
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myThumbnail.png', 'amp_thumbnail')
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myBrowse.png', 'amp_browse')
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myBrowse_rgb.png', 'rgb_browse')

    event = {'job_id': 'myJobId'}
    with patch('dynamo.jobs.update_job') as mock_update_job:
        get_files.lambda_handler(event, None)
        mock_update_job.assert_called_once_with(
            {
                'job_id': 'myJobId',
                'expiration_time': '2020-01-01T00:00:00+00:00',
                'files': [
                    {
                        'url': 'https://myBucket.s3.myRegion.amazonaws.com/myJobId/myProduct.zip',
                        's3': {
                            'bucket': 'myBucket',
                            'key': 'myJobId/myProduct.zip',
                        },
                        'size': 50,
                        'filename': 'myProduct.zip',
                    }
                ],
                'browse_images': [
                    'https://myBucket.s3.myRegion.amazonaws.com/myJobId/myBrowse.png',
                    'https://myBucket.s3.myRegion.amazonaws.com/myJobId/myBrowse_rgb.png',
                ],
                'thumbnail_images': ['https://myBucket.s3.myRegion.amazonaws.com/myJobId/myThumbnail.png'],
                'logs': [],
            }
        )


def test_get_files_netcdf_product(s3_stubber: Stubber):
    files = [
        {
            'Key': 'myJobId/myProduct.nc',
            'Size': 50,
        },
        {
            'Key': 'myJobId/myThumbnail.png',
            'Size': 5,
        },
        {
            'Key': 'myJobId/myBrowse.png',
            'Size': 10,
        },
    ]
    stub_list_files(s3_stubber, 'myJobId', 'myBucket', files)
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myProduct.nc', 'product')
    stub_expiration(s3_stubber, 'myBucket', 'myJobId/myProduct.nc')
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myThumbnail.png', 'amp_thumbnail')
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myBrowse.png', 'amp_browse')

    event = {'job_id': 'myJobId'}
    with patch('dynamo.jobs.update_job') as mock_update_job:
        get_files.lambda_handler(event, None)
        mock_update_job.assert_called_once_with(
            {
                'job_id': 'myJobId',
                'expiration_time': '2020-01-01T00:00:00+00:00',
                'files': [
                    {
                        'url': 'https://myBucket.s3.myRegion.amazonaws.com/myJobId/myProduct.nc',
                        's3': {
                            'bucket': 'myBucket',
                            'key': 'myJobId/myProduct.nc',
                        },
                        'size': 50,
                        'filename': 'myProduct.nc',
                    }
                ],
                'browse_images': [
                    'https://myBucket.s3.myRegion.amazonaws.com/myJobId/myBrowse.png',
                ],
                'thumbnail_images': ['https://myBucket.s3.myRegion.amazonaws.com/myJobId/myThumbnail.png'],
                'logs': [],
            }
        )


def test_get_files_failed_job(s3_stubber: Stubber):
    files = [
        {
            'Key': 'myJobId/myJobId.log',
            'Size': 10,
        },
    ]
    stub_list_files(s3_stubber, 'myJobId', 'myBucket', files)
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myJobId.log', 'log')
    stub_expiration(s3_stubber, 'myBucket', 'myJobId/myJobId.log')

    event = {'job_id': 'myJobId'}
    with patch('dynamo.jobs.update_job') as mock_update_job:
        get_files.lambda_handler(event, None)
        mock_update_job.assert_called_once_with(
            {
                'job_id': 'myJobId',
                'expiration_time': '2020-01-01T00:00:00+00:00',
                'files': [],
                'browse_images': [],
                'thumbnail_images': [],
                'logs': ['https://myBucket.s3.myRegion.amazonaws.com/myJobId/myJobId.log'],
            }
        )
