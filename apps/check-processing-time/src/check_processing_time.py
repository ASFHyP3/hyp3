import json


def get_time_from_attempts(attempts: list[dict]) -> float:
    if len(attempts) == 0:
        raise ValueError('no Batch job attempts')
    attempts.sort(key=lambda attempt: attempt['StoppedAt'])
    final_attempt = attempts[-1]
    return (final_attempt['StoppedAt'] - final_attempt['StartedAt']) / 1000


def get_time_from_result(result: dict) -> float:
    if 'Attempts' in result:
        attempts = result['Attempts']
    else:
        attempts = json.loads(result['Cause'])['Attempts']
    return get_time_from_attempts(attempts)


def lambda_handler(event, context):
    results = event['processing_results']
    return sum(map(get_time_from_result, results))
