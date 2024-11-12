from typing import Optional, Union


def get_time_from_result(result: Union[list, dict]) -> Union[list, float]:
    if isinstance(result, list):
        return [get_time_from_result(item) for item in result]

    processing_time = (result['StoppedAt'] - result['StartedAt']) / 1000

    if processing_time <= 0.0:
        raise ValueError(f'{processing_time} <= 0.0')

    return processing_time


def lambda_handler(event, _) -> Optional[list[Union[list, float]]]:
    processing_results = event['processing_results']
    result_list = [processing_results[key] for key in sorted(processing_results.keys())]
    return get_time_from_result(result_list)
