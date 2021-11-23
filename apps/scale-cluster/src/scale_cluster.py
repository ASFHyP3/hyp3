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


def get_month_to_date_ec2_spending():
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


def set_max_vcpus(compute_environment_arn, max_vcpus):
    print(f'Updating {compute_environment_arn} maxvCpus to {max_vcpus}')
    BATCH.update_compute_environment(
        computeEnvironment=compute_environment_arn,
        computeResources={'maxvCpus': max_vcpus},
    )


def get_max_vcpus(today, monthly_budget, month_to_date_spending, default_max_vcpus, expanded_max_vcpus,
                  required_surplus):
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    month_to_date_budget = (monthly_budget / days_in_month) * today.day
    available_surplus = (month_to_date_budget - month_to_date_spending)

    print(f'Month-to-date EC2 budget: ${month_to_date_budget:,.2f}')
    print(f'Month-to-date EC2 spending: ${month_to_date_spending:,.2f}')
    print(f'Available surplus: ${available_surplus:,.2f}')
    print(f'Required surplus: ${required_surplus:,.2f}')

    if available_surplus < required_surplus:
        max_vcpus = default_max_vcpus
    else:
        max_vcpus = expanded_max_vcpus
    return max_vcpus


def lambda_handler(event, context):
    max_vcpus = get_max_vcpus(today=date.today(),
                              monthly_budget=int(environ['MONTHLY_COMPUTE_BUDGET']),
                              month_to_date_spending=get_month_to_date_ec2_spending(),
                              default_max_vcpus=int(environ['DEFAULT_MAX_VCPUS']),
                              expanded_max_vcpus=int(environ['EXPANDED_MAX_VCPUS']),
                              required_surplus=int(environ['REQUIRED_SURPLUS']))
    set_max_vcpus(compute_environment_arn=environ['COMPUTE_ENVIRONMENT_ARN'], max_vcpus=max_vcpus)
