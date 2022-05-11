import pytest

import check_processing_time


def test_single_attempt():
    attempts = [{'Container': {}, 'StartedAt': 500, 'StatusReason': '', 'StoppedAt': 2800}]
    result = check_processing_time.get_time_from_attempts(attempts)
    assert result == 2.3


def test_multiple_attempts():
    attempts = [
        {'Container': {}, 'StartedAt': 500, 'StatusReason': '', 'StoppedAt': 1000},
        {'Container': {}, 'StartedAt': 3000, 'StatusReason': '', 'StoppedAt': 8700}
    ]
    result = check_processing_time.get_time_from_attempts(attempts)
    assert result == 5.7


def test_unsorted_attempts():
    # I'm not sure if the lambda would ever be given unsorted attempts, but it seems worth testing that it doesn't
    # depend on the list to be sorted.
    attempts = [
        {'Container': {}, 'StartedAt': 3000, 'StatusReason': '', 'StoppedAt': 8700},
        {'Container': {}, 'StartedAt': 500, 'StatusReason': '', 'StoppedAt': 1000}
    ]
    result = check_processing_time.get_time_from_attempts(attempts)
    assert result == 5.7


def test_missing_start_time():
    # There are some cases in which at least one of the attempts may not have a StartedAt time.
    # https://github.com/ASFHyP3/hyp3/issues/936
    attempts = [
        {'Container': {}, 'StartedAt': 500, 'StatusReason': '', 'StoppedAt': 1000},
        {'Container': {}, 'StatusReason': '', 'StoppedAt': 8700},
        {'Container': {}, 'StartedAt': 12000, 'StatusReason': '', 'StoppedAt': 15200}
    ]
    result = check_processing_time.get_time_from_attempts(attempts)
    assert result == 3.2


def test_no_attempts():
    with pytest.raises(ValueError, match='list of attempts is empty'):
        check_processing_time.get_time_from_attempts([])


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
    assert response == (1644611472015 - 1644610107570) / 1000


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
    assert response == (1643834908466 - 1643834907858) / 1000
