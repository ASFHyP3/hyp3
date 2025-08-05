import datetime
import unittest.mock
from decimal import Decimal

import search_archive


def test_aria_s1_gunw_exists(tables):
    tables.users_table.put_item(Item={'user_id': 'test-user', 'remaining_credits': Decimal(10)})
    tables.jobs_table.put_item(
        Item={
            'job_id': 'test-job',
            'status_code': 'PENDING',
            'credit_cost': Decimal(5),
        }
    )
    with (
        unittest.mock.patch.object(search_archive.aria_s1_gunw, 'get_product') as mock_get_product,
        unittest.mock.patch.object(search_archive, '_get_utc_time') as mock_get_utc_time,
    ):
        mock_archive_product = unittest.mock.MagicMock(
            properties={
                'browse': ['test-browse.png'],
                'fileName': 'test-file',
                'url': 'test-url',
            },
            umm={'DataGranule': {'ArchiveAndDistributionInformation': [{'SizeInBytes': 123}]}},
        )
        mock_get_product.return_value = mock_archive_product
        mock_get_utc_time.return_value = datetime.datetime(2025, 8, 4, 19, 1, 3, 700144, tzinfo=datetime.UTC)

        assert (
            search_archive.lambda_handler(
                {
                    'job_id': 'test-job',
                    'job_type': 'ARIA_S1_GUNW',
                    'job_parameters': {
                        'reference_date': '2019-12-31',
                        'secondary_date': '2018-12-12',
                        'frame_id': 11040,
                    },
                    'user_id': 'test-user',
                    'credit_cost': 5,
                },
                None,
            )
            is True
        )

        mock_get_product.assert_called_once_with(
            reference_date='2019-12-31',
            secondary_date='2018-12-12',
            frame_id=11040,
        )
        mock_get_utc_time.assert_called_once_with()

    assert tables.users_table.scan()['Items'] == [{'user_id': 'test-user', 'remaining_credits': Decimal(15)}]
    assert tables.jobs_table.scan()['Items'] == [
        {
            'job_id': 'test-job',
            'status_code': 'SUCCEEDED',
            'processing_times': [Decimal(0)],
            'credit_cost': Decimal(0),
            'browse_images': ['test-browse.png'],
            'expiration_time': '3022-03-11T19:01:03+00:00',
            'files': [
                {
                    'filename': 'test-file',
                    'size': Decimal(123),
                    'url': 'test-url',
                }
            ],
        }
    ]


def test_aria_s1_gunw_exists_infinite_credits(tables):
    tables.users_table.put_item(Item={'user_id': 'test-user', 'remaining_credits': None})
    tables.jobs_table.put_item(
        Item={
            'job_id': 'test-job',
            'status_code': 'PENDING',
            'credit_cost': Decimal(5),
        }
    )
    with (
        unittest.mock.patch.object(search_archive.aria_s1_gunw, 'get_product') as mock_get_product,
        unittest.mock.patch.object(search_archive, '_get_utc_time') as mock_get_utc_time,
    ):
        mock_archive_product = unittest.mock.MagicMock(
            properties={
                'browse': ['test-browse.png'],
                'fileName': 'test-file',
                'url': 'test-url',
            },
            umm={'DataGranule': {'ArchiveAndDistributionInformation': [{'SizeInBytes': 123}]}},
        )
        mock_get_product.return_value = mock_archive_product
        mock_get_utc_time.return_value = datetime.datetime(2025, 8, 4, 19, 1, 3, 700144, tzinfo=datetime.UTC)

        assert (
            search_archive.lambda_handler(
                {
                    'job_id': 'test-job',
                    'job_type': 'ARIA_S1_GUNW',
                    'job_parameters': {
                        'reference_date': '2019-12-31',
                        'secondary_date': '2018-12-12',
                        'frame_id': 11040,
                    },
                    'user_id': 'test-user',
                    'credit_cost': 5,
                },
                None,
            )
            is True
        )

        mock_get_product.assert_called_once_with(
            reference_date='2019-12-31',
            secondary_date='2018-12-12',
            frame_id=11040,
        )
        mock_get_utc_time.assert_called_once_with()

    assert tables.users_table.scan()['Items'] == [{'user_id': 'test-user', 'remaining_credits': None}]
    assert tables.jobs_table.scan()['Items'] == [
        {
            'job_id': 'test-job',
            'status_code': 'SUCCEEDED',
            'processing_times': [Decimal(0)],
            'credit_cost': Decimal(0),
            'browse_images': ['test-browse.png'],
            'expiration_time': '3022-03-11T19:01:03+00:00',
            'files': [
                {
                    'filename': 'test-file',
                    'size': Decimal(123),
                    'url': 'test-url',
                }
            ],
        }
    ]


def test_aria_s1_gunw_does_not_exist():
    with unittest.mock.patch.object(search_archive.aria_s1_gunw, 'get_product') as mock_get_product:
        mock_get_product.return_value = None

        assert (
            search_archive.lambda_handler(
                {
                    'job_id': 'test-job',
                    'job_type': 'ARIA_S1_GUNW',
                    'job_parameters': {
                        'reference_date': '2019-12-31',
                        'secondary_date': '2018-12-12',
                        'frame_id': 11040,
                    },
                },
                None,
            )
            is False
        )

        mock_get_product.assert_called_once_with(
            reference_date='2019-12-31',
            secondary_date='2018-12-12',
            frame_id=11040,
        )


def test_unsupported_job_type():
    assert (
        search_archive.lambda_handler(
            {
                'job_id': 'test-job',
                'job_type': 'test-job-type',
                'job_parameters': {},
            },
            None,
        )
        is False
    )
