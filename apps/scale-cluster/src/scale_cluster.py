import boto3
import dateutil.relativedelta
from datetime import date, datetime, timezone


def get_time_period(today: date):
    start = today.replace(day=1)
    end = start + dateutil.relativedelta.relativedelta(months=1)
    return {
        'Start': str(start),
        'End': str(end)
    }


def get_ec2_spending_month_to_date():
    client = boto3.client('ce')
    time_period = get_time_period(datetime.now(tz=timezone.utc).date())
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