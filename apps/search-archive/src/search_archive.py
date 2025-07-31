from datetime import UTC, datetime, timedelta
from decimal import Decimal

import asf_search as asf
from asf_enumeration import aria_s1_gunw

import dynamo


def _get_product_from_archive(job_type: str, job_parameters: dict) -> asf.ASFProduct | None:
    if job_type == 'ARIA_S1_GUNW':
        return aria_s1_gunw.get_product(
            reference_date=job_parameters['reference_date'],
            secondary_date=job_parameters['secondary_date'],
            frame_id=job_parameters['frame_id'],
        )
    else:
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


def lambda_handler(event: dict, _) -> bool:
    if product := _get_product_from_archive(event['job_type'], event['job_parameters']):
        _update_job(event['job_id'], product)
        dynamo.user.add_credits(event['user_id'], Decimal(event['credit_cost']))
        return True
    return False
