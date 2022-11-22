import logging
from functools import wraps

# TODO do we need to modify this since it's now in another module?
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
            raise

    return wrapper
