import check_processing_time


def test_single_attempt():
    attempts = [{'Container': {}, 'StartedAt': 1644423555778, 'StatusReason': '', 'StoppedAt': 1644425055200}]
    result = check_processing_time.get_time_from_attempts(attempts)
    assert result == 1644425055200 - 1644423555778


def test_multiple_attempts():
    attempts = [
        {'Container': {}, 'StartedAt': 1644609403693, 'StatusReason': '', 'StoppedAt': 1644609919331},
        {'Container': {}, 'StartedAt': 1644610107570, 'StatusReason': '', 'StoppedAt': 1644611472015}
    ]
    result = check_processing_time.get_time_from_attempts(attempts)
    assert result == 1644611472015 - 1644610107570


def test_unsorted_attempts():
    # I'm not sure if the lambda would ever be given unsorted attempts, but it seems worth testing that it doesn't
    # depend on the list to be sorted.
    attempts = [
        {'Container': {}, 'StartedAt': 1644610107570, 'StatusReason': '', 'StoppedAt': 1644611472015},
        {'Container': {}, 'StartedAt': 1644609403693, 'StatusReason': '', 'StoppedAt': 1644609919331}
    ]
    result = check_processing_time.get_time_from_attempts(attempts)
    assert result == 1644611472015 - 1644610107570


def test_lambda_handler_with_normal_results():
    event = {
        'processing_results': {
            'Attempts': [
                {'Container': {}, 'StartedAt': 1644609403693, 'StatusReason': '', 'StoppedAt': 1644609919331},
                {'Container': {}, 'StartedAt': 1644610107570, 'StatusReason': '', 'StoppedAt': 1644611472015}
            ]
        }
    }
    response = check_processing_time.lambda_handler(event, None)
    assert response == 1644611472015 - 1644610107570


def test_lambda_handler_with_failed_results():
    event = {
        'processing_results': {
            'Error': 'States.TaskFailed',
            'Cause': '{"Attempts": ['
                     '{"Container": {}, "StartedAt": 1643834765893, "StatusReason": "", "StoppedAt": 1643834766455}, '
                     '{"Container": {}, "StartedAt": 1643834888866, "StatusReason": "", "StoppedAt": 1643834889448}, '
                     '{"Container": {}, "StartedAt": 1643834907858, "StatusReason": "", "StoppedAt": 1643834908466}]}'
        }
    }
    response = check_processing_time.lambda_handler(event, None)
    assert response == 1643834908466 - 1643834907858
