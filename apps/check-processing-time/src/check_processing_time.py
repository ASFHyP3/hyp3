def lambda_handler(event, context):
    event['Attempts'].sort(key=lambda attempt: attempt['StartedAt'])
    final_attempt = event['Attempts'][-1]
    return final_attempt['StoppedAt'] - final_attempt['StartedAt']
