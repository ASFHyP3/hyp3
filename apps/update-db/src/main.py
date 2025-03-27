from dynamo import jobs


def lambda_handler(event: dict, context: object) -> None:
    jobs.update_job(event)
