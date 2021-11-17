import boto3
import datetime


def get_ec2_spending_month_to_date():
    client = boto3.client('ce')
    period = {
        'Start': '2021-10-01', # FIXME: Make this dynamic
        'End': '2021-11-01'
    }
    granularity = 'MONTHLY'
    _filter = {
        'Dimensions': {
            'Key': 'SERVICE',
            'Values': ['Amazon Elastic Compute Cloud - Compute', 'EC2 - Other']
        }
    }

    metrics = ['UnblendedCost']
    response = client.get_cost_and_usage(TimePeriod=period, Granularity=granularity, Filter=_filter, Metrics=metrics)
    return float(response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])


def lambda_handler(event, context):
    pass