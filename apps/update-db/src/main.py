from dynamo import jobs


def lambda_handler(event, context):
    job_id = event['job_id']
    update_dict = {k: v for k, v in event.items() if k != 'job-id'}
    jobs.update_job(
        job_id,
        update_dict
    )
