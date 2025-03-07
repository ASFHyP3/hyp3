import logging
from collections.abc import Callable
from functools import wraps
from typing import Any


logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class UnhandledException(Exception):
    pass


def log_exceptions[T](lambda_handler: Callable[[dict, Any], T]) -> Callable[[dict, Any], T]:
    @wraps(lambda_handler)
    def wrapper(event: dict, context: Any) -> T:
        try:
            return lambda_handler(event, context)
        except:  # noqa: E722
            logger.exception('Unhandled exception')
            raise UnhandledException('The Lambda function failed with an unhandled exception (see the logs)')

    return wrapper
