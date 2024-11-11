import pytest

import check_processing_time


def test_lambda_handler():
    event = {
        'processing_failed': False,
        'processing_results': {
            'step_0': {
                'StartedAt': 3000,
                'StoppedAt': 8700,
            },
            'step_1': {
                'StartedAt': 3000,
                'StoppedAt': 9400,
            },
            'step_2': [
                {
                    'StartedAt': 3000,
                    'StoppedAt': 8900,
                },
                {
                    'StartedAt': 4000,
                    'StoppedAt': 4200,
                },
            ]
        }
    }
    assert check_processing_time.lambda_handler(event, None) == [5.7, 6.4, [5.9, 0.2]]


def test_lambda_handler_invalid_result():
    event = {
        'processing_failed': False,
        'processing_results': {
            'step_0': {
                'StartedAt': 1000,
                'StoppedAt': 1000,
            }
        }
    }
    with pytest.raises(ValueError, match=r'^0.0 <= 0.0$'):
        check_processing_time.lambda_handler(event, None)

    event = {
        'processing_failed': False,
        'processing_results': {
            'step_0': {
                'StartedAt': 2000,
                'StoppedAt': 1000,
            }
        }
    }
    with pytest.raises(ValueError, match=r'^-1.0 <= 0.0$'):
        check_processing_time.lambda_handler(event, None)

    event = {
        'processing_failed': False,
        'processing_results': {
            'step_0': {
                'StartedAt': 3000,
                'StoppedAt': 8700,
            },
            'step_1': [
                {
                    'StartedAt': 3000,
                    'StoppedAt': 8900,
                },
                {
                    'StartedAt': 4200,
                    'StoppedAt': 4000,
                },
            ]
        }
    }
    with pytest.raises(ValueError, match=r'^-0.2 <= 0.0$'):
        check_processing_time.lambda_handler(event, None)


def test_lambda_handler_failed_job():
    event = {
        'processing_failed': True,
        'processing_results': {
            'step_0': {
                'StartedAt': 3000,
                'StoppedAt': 8700,
            },
        }
    }
    assert check_processing_time.lambda_handler(event, None) is None
