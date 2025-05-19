from typing import Any

import pytest

import lambda_logging


def test_log_exceptions_error():
    @lambda_logging.log_exceptions
    def lambda_handler(event: dict, context: Any) -> None:
        raise ValueError()

    with pytest.raises(ValueError):
        lambda_handler.__wrapped__({}, None)  # type: ignore[attr-defined]

    with pytest.raises(lambda_logging.UnhandledException):
        lambda_handler({}, None)


def test_log_exceptions_return():
    @lambda_logging.log_exceptions
    def lambda_handler(event: dict, context: Any) -> str:
        return 'foo'

    assert lambda_handler({}, None) == 'foo'
