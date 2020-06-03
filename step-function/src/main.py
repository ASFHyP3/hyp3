from os import environ

import boto3

DB = boto3.resource('dynamodb')
PRIMARY_KEY = 'job_id'


def lambda_handler(event, context):
    table = DB.Table(environ['TABLE_NAME'])

    key = {PRIMARY_KEY: event[PRIMARY_KEY]}
    update_expression = 'SET {}'.format(','.join(f'{k}=:{k}' for k in event if k != PRIMARY_KEY))
    expression_attribute_values = {f':{k}': v for k, v in event.items() if k != PRIMARY_KEY}

    table.update_item(
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values,
    )
