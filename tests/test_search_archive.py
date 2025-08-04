import search_archive


def test_aria_s1_gunw_exists():
    assert False


def test_aria_s1_gunw_does_not_exist():
    assert False


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
