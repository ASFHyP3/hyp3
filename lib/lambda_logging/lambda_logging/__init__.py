import logging
import sys
from functools import wraps

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def log_exceptions(lambda_handler):

    @wraps(lambda_handler)
    def wrapper(event, context):
        try:
            lambda_handler(event, context)
        except:  # noqa: E722
            logger.exception('Unhandled exception')
            sys.exit(1)

    return wrapper
