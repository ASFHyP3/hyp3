import logging
from collections.abc import Callable
from functools import wraps


logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class UnhandledException(Exception):
    pass


def log_exceptions[EventType, ReturnType](
    lambda_handler: Callable[[EventType, object], ReturnType],
) -> Callable[[EventType, object], ReturnType]:
    @wraps(lambda_handler)
    def wrapper(event: EventType, context: object) -> ReturnType:
        try:
            return lambda_handler(event, context)
        except:  # noqa: E722
            logger.exception('Unhandled exception')
            raise UnhandledException('The Lambda function failed with an unhandled exception (see the logs)')

    return wrapper
