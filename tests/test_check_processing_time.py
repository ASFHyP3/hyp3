import check_processing_time


def test_single_attempt():
    attempts = [{'Container': {}, 'StartedAt': 500, 'StatusReason': '', 'StoppedAt': 2800}]
    assert check_processing_time.get_time_from_attempts(attempts) == 2.3


def test_multiple_attempts():
    attempts = [
        {'Container': {}, 'StartedAt': 500, 'StatusReason': '', 'StoppedAt': 1000},
        {'Container': {}, 'StartedAt': 3000, 'StatusReason': '', 'StoppedAt': 8700}
    ]
    assert check_processing_time.get_time_from_attempts(attempts) == 5.7


def test_unsorted_attempts():
    # I'm not sure if the lambda would ever be given unsorted attempts, but it seems worth testing that it doesn't
    # depend on the list to be sorted.
    attempts = [
        {'Container': {}, 'StartedAt': 3000, 'StatusReason': '', 'StoppedAt': 8700},
        {'Container': {}, 'StartedAt': 500, 'StatusReason': '', 'StoppedAt': 1000}
    ]
    assert check_processing_time.get_time_from_attempts(attempts) == 5.7


def test_missing_start_time():
    # There are some cases in which at least one of the attempts may not have a StartedAt time.
    # https://github.com/ASFHyP3/hyp3/issues/936
    attempts = [
        {'Container': {}, 'StartedAt': 500, 'StatusReason': '', 'StoppedAt': 1000},
        {'Container': {}, 'StatusReason': '', 'StoppedAt': 8700},
        {'Container': {}, 'StartedAt': 12000, 'StatusReason': '', 'StoppedAt': 15200}
    ]
    assert check_processing_time.get_time_from_attempts(attempts) == 3.2


def test_no_attempts():
    assert check_processing_time.get_time_from_attempts([]) == 0


def test_get_time_from_result():
    result = {
        'Attempts': [
            {'Container': {}, 'StartedAt': 500, 'StatusReason': '', 'StoppedAt': 1000},
            {'Container': {}, 'StartedAt': 3000, 'StatusReason': '', 'StoppedAt': 8700}
        ]
    }
    assert check_processing_time.get_time_from_result(result) == 5.7


def test_get_time_from_result_list():
    result = [
        {
            'Attempts': [
                {'Container': {}, 'StartedAt': 500, 'StatusReason': '', 'StoppedAt': 1000},
                {'Container': {}, 'StartedAt': 3000, 'StatusReason': '', 'StoppedAt': 8900}
            ]
        },
        {
            'Attempts': [
                {'Container': {}, 'StartedAt': 500, 'StatusReason': '', 'StoppedAt': 3000},
                {'Container': {}, 'StartedAt': 4000, 'StatusReason': '', 'StoppedAt': 4200}
            ]
        },
    ]
    assert check_processing_time.get_time_from_result(result) == [5.9, 0.2]


def test_get_time_from_result_failed():
    result = {
        'Error': 'States.TaskFailed',
        'Cause': '{"Attempts": ['
                 '{"Container": {}, "StartedAt": 500, "StatusReason": "", "StoppedAt": 1000}, '
                 '{"Container": {}, "StartedAt": 1500, "StatusReason": "", "StoppedAt": 2000}, '
                 '{"Container": {}, "StartedAt": 3000, "StatusReason": "", "StoppedAt": 9400}]}'
    }
    assert check_processing_time.get_time_from_result(result) == 6.4


def test_lambda_handler():
    event = {
        'processing_results': {
            'step_0': {
                'Attempts': [
                    {'Container': {}, 'StartedAt': 500, 'StatusReason': '', 'StoppedAt': 1000},
                    {'Container': {}, 'StartedAt': 3000, 'StatusReason': '', 'StoppedAt': 8700}
                ]
            },
            'step_1': {
                'Error': 'States.TaskFailed',
                'Cause': '{"Attempts": ['
                         '{"Container": {}, "StartedAt": 500, "StatusReason": "", "StoppedAt": 1000}, '
                         '{"Container": {}, "StartedAt": 1500, "StatusReason": "", "StoppedAt": 2000}, '
                         '{"Container": {}, "StartedAt": 3000, "StatusReason": "", "StoppedAt": 9400}]}'
            },
            'step_2': [
                {
                    'Attempts': [
                        {'Container': {}, 'StartedAt': 500, 'StatusReason': '', 'StoppedAt': 1000},
                        {'Container': {}, 'StartedAt': 3000, 'StatusReason': '', 'StoppedAt': 8900}
                    ]
                },
                {
                    'Attempts': [
                        {'Container': {}, 'StartedAt': 500, 'StatusReason': '', 'StoppedAt': 3000},
                        {'Container': {}, 'StartedAt': 4000, 'StatusReason': '', 'StoppedAt': 4200}
                    ]
                },
            ]
        }
    }
    assert check_processing_time.lambda_handler(event, None) == [5.7, 6.4, [5.9, 0.2]]
