def lambda_handler(event, context) -> bool:
    return any('Error' in result for result in event['processing_results'].values())
