import json
from typing import Union


def get_time_from_attempts(attempts: list[dict]) -> float:
    if len(attempts) == 0:
        return 0
    attempts.sort(key=lambda attempt: attempt['StoppedAt'])
    final_attempt = attempts[-1]
    return (final_attempt['StoppedAt'] - final_attempt['StartedAt']) / 1000


def get_time_from_result(result: Union[list, dict]) -> Union[list, float]:
    if isinstance(result, list):
        return [get_time_from_result(item) for item in result]

    if 'start' in result:
        attempts = [{'StartedAt': start, 'StoppedAt': stop} for start, stop in zip(result['start'], result['stop'])]
        return get_time_from_attempts(attempts)

    return get_time_from_attempts(json.loads(result['Cause'])['Attempts'])


def lambda_handler(event, _) -> list[Union[list, float]]:
    processing_results = event['processing_results']
    result_list = [processing_results[key] for key in sorted(processing_results.keys())]
    return get_time_from_result(result_list)
