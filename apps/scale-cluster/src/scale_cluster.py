import boto3
from datetime import datetime, timezone

def get_time_period():
    today = datetime.now(tz=timezone.utc).date()
    start = today.replace(day=1)
    next_month = 1 if start.month == 12 else start.month + 1
    end = start.replace(month=next_month)
    return {
        'Start': str(start),
        'End': str(end)
    }


def get_ec2_spending_month_to_date():
    client = boto3.client('ce')
    time_period = get_time_period()
    granularity = 'MONTHLY'
    _filter = {
        'Dimensions': {
            'Key': 'SERVICE',
            'Values': ['Amazon Elastic Compute Cloud - Compute', 'EC2 - Other']
        }
    }
    metrics = ['UnblendedCost']
    response = client.get_cost_and_usage(TimePeriod=time_period, Granularity=granularity, Filter=_filter, Metrics=metrics)
    return float(response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])


def lambda_handler(event, context):
    pass