from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TypedDict

import asf_search as asf
from asf_enumeration import aria_s1_gunw

import dynamo
from dynamo.exceptions import AddToInfiniteCreditsError
from lambda_logging import log_exceptions, logger


def _get_product_from_archive(job_type: str, job_parameters: dict) -> asf.ASFProduct | None:
    if job_type == 'ARIA_S1_GUNW':
        logger.info(f'Searching archive for {job_type} product')
        return aria_s1_gunw.get_product(
            reference_date=job_parameters['reference_date'],
            secondary_date=job_parameters['secondary_date'],
            frame_id=job_parameters['frame_id'],
        )
    else:
        logger.info(f'Searching archive is not supported for {job_type}')
        return None


def _get_utc_time() -> datetime:
    return datetime.now(UTC)


def _update_job(job_id: str, product: asf.ASFProduct) -> None:
    expiration_datetime = _get_utc_time() + timedelta(weeks=1000 * 52)
    dynamo.jobs.update_job(
        {
            'job_id': job_id,
            'status_code': 'SUCCEEDED',
            'processing_times': [0],
            'credit_cost': 0,
            'browse_images': product.properties['browse'],
            'expiration_time': expiration_datetime.isoformat(timespec='seconds'),
            'files': [
                {
                    'filename': product.properties['fileName'],
                    'size': product.umm['DataGranule']['ArchiveAndDistributionInformation'][0]['SizeInBytes'],
                    'url': product.properties['url'],
                }
            ],
        }
    )


class SearchArchiveEvent(TypedDict):
    job_id: str
    job_type: str
    job_parameters: dict
    user_id: str
    credit_cost: int | float


@log_exceptions
def lambda_handler(event: Event, _) -> bool:
    logger.info(event)

    if product := _get_product_from_archive(event['job_type'], event['job_parameters']):
        logger.info(f'Found product, updating job {event["job_id"]}')
        _update_job(event['job_id'], product)

        logger.info(f'Refunding {event["credit_cost"]} credits to user {event["user_id"]}')
        try:
            dynamo.user.add_credits(event['user_id'], Decimal(str(event['credit_cost'])))
        except AddToInfiniteCreditsError:
            logger.info(f'User {event["user_id"]} has infinite credits')

        return True

    logger.info(f'No archived product exists for job {event["job_id"]}')
    return False
