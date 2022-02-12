import check_processing_time


def test_single_attempt():
    event = {
        'Attempts': [{'Container': {}, 'StartedAt': 1644423555778, 'StatusReason': '', 'StoppedAt': 1644425055200}]
    }
    response = check_processing_time.lambda_handler(event, None)
    assert response == 1644425055200 - 1644423555778


def test_multiple_attempts():
    event = {
        'Attempts': [
            {'Container': {}, 'StartedAt': 1644609403693, 'StatusReason': '', 'StoppedAt': 1644609919331},
            {'Container': {}, 'StartedAt': 1644610107570, 'StatusReason': '', 'StoppedAt': 1644611472015}
        ]
    }
    response = check_processing_time.lambda_handler(event, None)
    assert response == 1644611472015 - 1644610107570


def test_unsorted_attempts():
    # I'm not sure if the lambda would ever be given unsorted attempts, but it seems worth testing that it doesn't
    # depend on the list to be sorted.
    event = {
        'Attempts': [
            {'Container': {}, 'StartedAt': 1644610107570, 'StatusReason': '', 'StoppedAt': 1644611472015},
            {'Container': {}, 'StartedAt': 1644609403693, 'StatusReason': '', 'StoppedAt': 1644609919331}
        ]
    }
    response = check_processing_time.lambda_handler(event, None)
    assert response == 1644611472015 - 1644610107570
