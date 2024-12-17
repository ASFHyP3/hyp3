import lambda_logging
import pytest


def test_log_exceptions():
    @lambda_logging.log_exceptions
    def lambda_handler(event, context):
        raise ValueError()

    with pytest.raises(ValueError):
        lambda_handler.__wrapped__(None, None)

    with pytest.raises(lambda_logging.UnhandledException):
        lambda_handler(None, None)
