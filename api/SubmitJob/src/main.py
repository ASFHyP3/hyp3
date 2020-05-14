import boto3

client = boto3.client('batch')
def lambda_handler(event, context):
    client.submit_job(event['body']['granule'], )
