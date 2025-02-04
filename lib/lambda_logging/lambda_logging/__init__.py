import logging
from functools import wraps


logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class UnhandledException(Exception):
    pass


def log_exceptions(lambda_handler):
    @wraps(lambda_handler)
    def wrapper(event, context):
        try:
            lambda_handler(event, context)
        except:  # noqa: E722
            logger.exception('Unhandled exception')
            raise UnhandledException('The Lambda function failed with an unhandled exception (see the logs)')

    return wrapper
