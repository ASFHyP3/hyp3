from datetime import UTC, datetime, timedelta
from decimal import Decimal

import asf_search as asf
from asf_enumeration import aria_s1_gunw

import dynamo
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


def _update_job(job_id: str, product: asf.ASFProduct) -> None:
    expiration_datetime = datetime.now(UTC) + timedelta(weeks=1000 * 52)
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


@log_exceptions
def lambda_handler(event: dict, _) -> bool:
    logger.info(event)

    if product := _get_product_from_archive(event['job_type'], event['job_parameters']):
        logger.info(f'Found product, updating job {event["job_id"]}')
        _update_job(event['job_id'], product)

        logger.info(f'Refunding {event["credit_cost"]} credits to user {event["user_id"]}')
        dynamo.user.add_credits(event['user_id'], Decimal(event['credit_cost']))

        return True

    logger.info(f'No archived product exists for job {event["job_id"]}')
    return False
