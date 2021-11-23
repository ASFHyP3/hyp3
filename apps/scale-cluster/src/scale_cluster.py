import calendar
from datetime import date
from os import environ

import boto3
import dateutil.relativedelta

BATCH = boto3.client('batch')
COST_EXPLORER = boto3.client('ce')


def get_time_period(today: date):
    start = today.replace(day=1)
    end = start + dateutil.relativedelta.relativedelta(months=1)
    return {
        'Start': str(start),
        'End': str(end)
    }


def get_ec2_spending_month_to_date():
    time_period = get_time_period(date.today())
    granularity = 'MONTHLY'
    _filter = {
        'Dimensions': {
            'Key': 'SERVICE',
            'Values': ['Amazon Elastic Compute Cloud - Compute', 'EC2 - Other']
        }
    }
    metrics = ['UnblendedCost']
    response = COST_EXPLORER.get_cost_and_usage(TimePeriod=time_period, Granularity=granularity, Filter=_filter,
                                                Metrics=metrics)
    return float(response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])


def update_compute_cluster_size(max_vcpus):
    compute_environment_arn = environ['COMPUTE_ENVIRONMENT_ARN']
    print(f'Updating {compute_environment_arn} maxvCpus to {max_vcpus}')
    BATCH.update_compute_environment(
        computeEnvironment=compute_environment_arn,
        computeResources={'maxvCpus': max_vcpus},
    )


def get_max_vcpus(today, budget, spending, default_max_vcpus, expanded_max_vcpus, required_surplus):
    days_in_month = calendar.monthrange(today.year, today.month)[1]

    target_spending = (budget / days_in_month) * today.day
    max_spending_for_next_day = (target_spending - spending)

    if max_spending_for_next_day >= required_surplus:
        max_vcpus = expanded_max_vcpus
    else:
        max_vcpus = default_max_vcpus
    return max_vcpus


def lambda_handler(event, context):
    max_vcpus = get_max_vcpus(today=date.today(),
                              budget=int(environ['MONTHLY_COMPUTE_BUDGET']),
                              spending=get_ec2_spending_month_to_date(),
                              default_max_vcpus=int(environ['DEFAULT_MAX_VCPUS']),
                              expanded_max_vcpus=int(environ['EXPANDED_MAX_VCPUS']),
                              required_surplus=int(environ['REQUIRED_SURPLUS']))
    update_compute_cluster_size(max_vcpus)
