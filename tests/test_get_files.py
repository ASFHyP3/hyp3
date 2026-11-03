import io
import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from botocore.response import StreamingBody
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


def stub_bucket_head(s3_stubber: Stubber, bucket, region):
    params = {'Bucket': bucket}
    s3_response = {'BucketRegion': region}
    s3_stubber.add_response(method='head_bucket', expected_params=params, service_response=s3_response)


def test_get_download_url(monkeypatch, s3_stubber: Stubber):
    assert os.getenv('DISTRIBUTION_URL') is None
    stub_bucket_head(s3_stubber, 'myBucket', 'myRegion')
    assert get_files.get_download_url('myBucket', 'myKey') == 'https://myBucket.s3.myRegion.amazonaws.com/myKey'

    monkeypatch.setenv('DISTRIBUTION_URL', '')
    stub_bucket_head(s3_stubber, 'myBucket', 'myRegion')
    assert get_files.get_download_url('myBucket', 'myKey') == 'https://myBucket.s3.myRegion.amazonaws.com/myKey'

    monkeypatch.setenv('DISTRIBUTION_URL', 'https://foo.com/')
    assert get_files.get_download_url('myBucket', 'myKey') == 'https://foo.com/myKey'

    monkeypatch.setenv('DISTRIBUTION_URL', 'https://foo.com')
    assert get_files.get_download_url('myBucket', 'myKey') == 'https://foo.com/myKey'

    stub_bucket_head(s3_stubber, 'userBucket', 'userRegion')
    assert get_files.get_download_url('userBucket', 'myKey') == 'https://userBucket.s3.userRegion.amazonaws.com/myKey'

    monkeypatch.delenv('DISTRIBUTION_URL')
    stub_bucket_head(s3_stubber, 'userBucket', 'userRegion')
    assert get_files.get_download_url('userBucket', 'myKey') == 'https://userBucket.s3.userRegion.amazonaws.com/myKey'


def stub_expiration(s3_stubber: Stubber, bucket, key, expires=True):
    params = {'Bucket': bucket, 'Key': key}
    s3_response = {}
    if expires:
        s3_response['Expiration'] = (
            'expiry-date="Wed, 01 Jan 2020 00:00:00 UTC", rule-id="MDQxMzRmZTgtNDFlMi00Y2UwLWIyZjEtMTEzYTllNDNjYjJk"'
        )

    s3_stubber.add_response(method='get_object', expected_params=params, service_response=s3_response)


def test_get_expiration(s3_stubber: Stubber):
    stub_expiration(s3_stubber, 'myBucket', 'myKey', expires=True)
    response = get_files.get_expiration_time('myBucket', 'myKey')
    assert response == '2020-01-01T00:00:00+00:00'

    stub_expiration(s3_stubber, 'userBucket', 'userKey', expires=False)
    response = get_files.get_expiration_time('userBucket', 'userKey')
    assert response == '2120-10-21T00:00:00+00:00'


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
    stub_bucket_head(s3_stubber, 'myBucket', 'myRegion')
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myProduct.zip', 'product')
    stub_expiration(s3_stubber, 'myBucket', 'myJobId/myProduct.zip')
    stub_bucket_head(s3_stubber, 'myBucket', 'myRegion')
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myProduct.tif', 'product')
    stub_bucket_head(s3_stubber, 'myBucket', 'myRegion')
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myThumbnail.png', 'amp_thumbnail')
    stub_bucket_head(s3_stubber, 'myBucket', 'myRegion')
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myBrowse.png', 'amp_browse')
    stub_bucket_head(s3_stubber, 'myBucket', 'myRegion')
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myBrowse_rgb.png', 'rgb_browse')

    event = {'job_id': 'myJobId', 'bucket': 'myBucket', 'bucket_prefix': 'myJobId'}
    with patch('dynamo.jobs.get_job') as mock_get_job:
        with patch('dynamo.jobs.update_job') as mock_update_job:
            mock_get_job.return_value = {
                'job_id': 'myJobId',
                'bucket': 'myBucket',
                'bucket_prefix': 'myJobId',
            }
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
    stub_bucket_head(s3_stubber, 'myBucket', 'myRegion')
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myProduct.nc', 'product')
    stub_expiration(s3_stubber, 'myBucket', 'myJobId/myProduct.nc')
    stub_bucket_head(s3_stubber, 'myBucket', 'myRegion')
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myThumbnail.png', 'amp_thumbnail')
    stub_bucket_head(s3_stubber, 'myBucket', 'myRegion')
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myBrowse.png', 'amp_browse')

    event = {'job_id': 'myJobId', 'bucket': 'myBucket', 'bucket_prefix': 'myJobId'}
    with patch('dynamo.jobs.get_job') as mock_get_job:
        with patch('dynamo.jobs.update_job') as mock_update_job:
            mock_get_job.return_value = {
                'job_id': 'myJobId',
                'bucket': 'myBucket',
                'bucket_prefix': 'myJobId',
            }
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
    stub_bucket_head(s3_stubber, 'myBucket', 'myRegion')
    stub_get_object_tagging(s3_stubber, 'myBucket', 'myJobId/myJobId.log', 'log')
    stub_expiration(s3_stubber, 'myBucket', 'myJobId/myJobId.log')

    event = {'job_id': 'myJobId', 'bucket': 'myBucket', 'bucket_prefix': 'myJobId'}
    with patch('dynamo.jobs.get_job') as mock_get_job:
        with patch('dynamo.jobs.update_job') as mock_update_job:
            mock_get_job.return_value = {
                'job_id': 'myJobId',
                'bucket': 'myBucket',
                'bucket_prefix': 'myJobId',
            }
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


def stub_get_stac_object(s3_stubber, bucket, key, stac_path):
    data = stac_path.read_bytes()
    s3_stubber.add_response(
        'get_object',
        {'Body': StreamingBody(io.BytesIO(data), len(data))},
        {'Bucket': bucket, 'Key': key},
    )


def test_organize_files_stac(s3_stubber, stac_nisar_cv):
    stac_key = 'myJobId/nisar-cv-test-docker-container.stac.json'
    cv_key = 'myJobId/NISAR_148_A_024_HHHH_20260624_20260811_CV.tif'
    cv_100m_key = 'myJobId/NISAR_148_A_024_HHHH_20260624_20260811_CV_100m.tif'
    nvalid_key = 'myJobId/NISAR_148_A_024_HHHH_20260624_20260811_NVALID.tif'
    water_key = 'myJobId/NISAR_148_A_024_HHHH_20260624_20260811_WATER.tif'
    crop_key = 'myJobId/NISAR_148_A_024_HHHH_20260624_20260811_CROP_100m.tif'

    s3_objects: list[get_files.S3Object] = [
        {'Key': stac_key, 'Size': 2000},
        {'Key': cv_key, 'Size': 100},
        {'Key': cv_100m_key, 'Size': 50},
        {'Key': nvalid_key, 'Size': 25},
        {'Key': water_key, 'Size': 30},
        {'Key': crop_key, 'Size': 35},
    ]

    stub_get_stac_object(s3_stubber, 'myBucket', stac_key, stac_nisar_cv)
    for _ in range(5):
        stub_bucket_head(s3_stubber, 'myBucket', 'myRegion')

    result = get_files.organize_files_stac(s3_objects, 'myBucket')

    base = 'https://myBucket.s3.myRegion.amazonaws.com'
    expected: get_files.StacFiles = {
        'files': [
            {
                'url': f'{base}/myJobId/NISAR_148_A_024_HHHH_20260624_20260811_CV.tif',
                'size': 100,
                'filename': 'NISAR_148_A_024_HHHH_20260624_20260811_CV.tif',
                's3': {
                    'bucket': 'myBucket',
                    'key': 'myJobId/NISAR_148_A_024_HHHH_20260624_20260811_CV.tif',
                },
            },
            {
                'url': f'{base}/myJobId/NISAR_148_A_024_HHHH_20260624_20260811_CV_100m.tif',
                'size': 50,
                'filename': 'NISAR_148_A_024_HHHH_20260624_20260811_CV_100m.tif',
                's3': {
                    'bucket': 'myBucket',
                    'key': 'myJobId/NISAR_148_A_024_HHHH_20260624_20260811_CV_100m.tif',
                },
            },
            {
                'url': f'{base}/myJobId/NISAR_148_A_024_HHHH_20260624_20260811_NVALID.tif',
                'size': 25,
                'filename': 'NISAR_148_A_024_HHHH_20260624_20260811_NVALID.tif',
                's3': {
                    'bucket': 'myBucket',
                    'key': 'myJobId/NISAR_148_A_024_HHHH_20260624_20260811_NVALID.tif',
                },
            },
            {
                'url': f'{base}/myJobId/NISAR_148_A_024_HHHH_20260624_20260811_WATER.tif',
                'size': 30,
                'filename': 'NISAR_148_A_024_HHHH_20260624_20260811_WATER.tif',
                's3': {
                    'bucket': 'myBucket',
                    'key': 'myJobId/NISAR_148_A_024_HHHH_20260624_20260811_WATER.tif',
                },
            },
            {
                'url': f'{base}/myJobId/NISAR_148_A_024_HHHH_20260624_20260811_CROP_100m.tif',
                'size': 35,
                'filename': 'NISAR_148_A_024_HHHH_20260624_20260811_CROP_100m.tif',
                's3': {
                    'bucket': 'myBucket',
                    'key': 'myJobId/NISAR_148_A_024_HHHH_20260624_20260811_CROP_100m.tif',
                },
            },
        ],
        'browse_images': [
            'https://myBucket.s3.myRegion.amazonaws.com/myJobId/NISAR_148_A_024_HHHH_20260624_20260811_CV_100m.tif',
            'https://myBucket.s3.myRegion.amazonaws.com/myJobId/NISAR_148_A_024_HHHH_20260624_20260811_CROP_100m.tif',
        ],
        'thumbnail_images': [],
    }

    assert result == expected


def test_organize_files_stac_itslive(s3_stubber, stac_itslive):
    stac_key = 'myJobId/itslive.stac.json'
    data_key = (
        'myJobId/LC08_L1GT_020121_20231013_20231102_02_T2_X_LC09_L1GT_020121_20231106_20231106_02_T2_G0120V02_P084.nc'
    )
    overview_key = (
        'myJobId/LC08_L1GT_020121_20231013_20231102_02_T2_X_LC09_L1GT_020121_20231106_20231106_02_T2_G0120V02_P084.png'
    )
    thumbnail_key = 'myJobId/LC08_L1GT_020121_20231013_20231102_02_T2_X_LC09_L1GT_020121_20231106_20231106_02_T2_G0120V02_P084_thumb.png'

    s3_objects: list[get_files.S3Object] = [
        {'Key': stac_key, 'Size': 20},
        {'Key': data_key, 'Size': 100},
        {'Key': overview_key, 'Size': 50},
        {'Key': thumbnail_key, 'Size': 25},
    ]

    stub_get_stac_object(s3_stubber, 'myBucket', stac_key, stac_itslive)
    for _ in range(3):
        stub_bucket_head(s3_stubber, 'myBucket', 'myRegion')

    result = get_files.organize_files_stac(s3_objects, 'myBucket')

    base = 'https://myBucket.s3.myRegion.amazonaws.com'
    expected: get_files.StacFiles = {
        'files': [
            {
                'url': f'{base}/myJobId/LC08_L1GT_020121_20231013_20231102_02_T2_X_LC09_L1GT_020121_20231106_20231106_02_T2_G0120V02_P084.nc',
                'size': 100,
                'filename': 'LC08_L1GT_020121_20231013_20231102_02_T2_X_LC09_L1GT_020121_20231106_20231106_02_T2_G0120V02_P084.nc',
                's3': {
                    'bucket': 'myBucket',
                    'key': 'myJobId/LC08_L1GT_020121_20231013_20231102_02_T2_X_LC09_L1GT_020121_20231106_20231106_02_T2_G0120V02_P084.nc',
                },
            },
        ],
        'browse_images': [
            f'{base}/myJobId/LC08_L1GT_020121_20231013_20231102_02_T2_X_LC09_L1GT_020121_20231106_20231106_02_T2_G0120V02_P084.png'
        ],
        'thumbnail_images': [
            f'{base}/myJobId/LC08_L1GT_020121_20231013_20231102_02_T2_X_LC09_L1GT_020121_20231106_20231106_02_T2_G0120V02_P084_thumb.png'
        ],
    }

    assert result == expected


@pytest.fixture
def stac_nisar_cv(tmp_path):
    asset_path = Path(__file__).parent / 'assets' / 'stac' / 'nisar-cv.stac.json'
    path = tmp_path / 'nisar-cv.stac.json'
    shutil.copy2(asset_path, path)

    return path


@pytest.fixture
def stac_itslive(tmp_path):
    asset_path = Path(__file__).parent / 'assets' / 'stac' / 'itslive.stac.json'
    path = tmp_path / 'itslive.stac.json'
    shutil.copy2(asset_path, path)

    return path
