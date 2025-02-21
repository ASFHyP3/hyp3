import dynamo


def validate_field(actual: object, expected: object, field_name: str) -> None:
    if actual != expected:
        raise ValueError(f"Expected {field_name} '{expected}' but got '{actual}'.")


def lambda_handler(event: dict, _) -> None:
    validate_field(event['source'], 'aws.batch', 'source')
    validate_field(event['detail-type'], 'Batch Job State Change', 'detail-type')
    validate_field(event['detail']['status'], 'RUNNING', 'status')

    job_id = event['detail']['jobName']
    job = dynamo.jobs.get_job(job_id)

    assert job['job_id'] == job_id

    if job['status_code'] == 'PENDING':
        updated_job = {'job_id': job_id, 'status_code': 'RUNNING'}
        print(f'Updating job: {updated_job}')
        dynamo.jobs.update_job(updated_job)
    else:
        print(f'Job {job_id} status is {job["status_code"]} so job will not be updated')
