import check_processing_time


def test_lambda_handler():
    event = {
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
