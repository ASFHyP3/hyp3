

def get_time_from_result(result: list | dict) -> list | float:
    if isinstance(result, list):
        return [get_time_from_result(item) for item in result]

    return (result['StoppedAt'] - result['StartedAt']) / 1000


def lambda_handler(event, _) -> list | float:
    processing_results = event['processing_results']
    result_list = [processing_results[key] for key in sorted(processing_results.keys())]
    return get_time_from_result(result_list)
