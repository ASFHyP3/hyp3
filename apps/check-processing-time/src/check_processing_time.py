import json


def get_time_from_attempts(attempts):
    attempts.sort(key=lambda attempt: attempt['StartedAt'])
    final_attempt = attempts[-1]
    return final_attempt['StoppedAt'] - final_attempt['StartedAt']


def lambda_handler(event, context):
    results = event['processing_results']
    if 'Attempts' in results:
        return get_time_from_attempts(results['Attempts'])
    return get_time_from_attempts(json.loads(results['Cause'])['Attempts'])
