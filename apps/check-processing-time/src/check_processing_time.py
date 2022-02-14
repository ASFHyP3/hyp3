def lambda_handler(event, context):
    results = event['processing_results']
    results['Attempts'].sort(key=lambda attempt: attempt['StartedAt'])
    final_attempt = results['Attempts'][-1]
    return final_attempt['StoppedAt'] - final_attempt['StartedAt']
