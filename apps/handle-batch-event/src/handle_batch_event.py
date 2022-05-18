import dynamo


def validate_field(actual, expected, field_name: str) -> None:
    if actual != expected:
        raise ValueError(f"Expected {field_name} '{expected}' but got '{actual}'.")


def lambda_handler(event, context):
    validate_field(event['source'], 'aws.batch', 'source')
    validate_field(event['detail-type'], 'Batch Job State Change', 'detail-type')
    validate_field(event['detail']['status'], 'RUNNING', 'status')

    job = {'job_id': event['detail']['jobName'], 'status_code': 'RUNNING'}
    print(f'Updating job: {job}')
    dynamo.jobs.update_job(job)
