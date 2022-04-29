def lambda_handler(event, context):
    source = event['source']
    detail_type = event['detail-type']
    status = event['detail']['status']

    assert source == 'aws.batch', source
    assert detail_type == 'Batch Job State Change', detail_type
    assert status == 'RUNNING', status

    print(f'EVENT STATUS: {status}')
