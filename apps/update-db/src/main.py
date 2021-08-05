from dynamo import jobs


def lambda_handler(event, context):
    jobs.update_job(event)
