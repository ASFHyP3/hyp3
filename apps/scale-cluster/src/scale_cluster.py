import calendar
from datetime import date
from os import environ

import boto3
import dateutil.relativedelta


BATCH = boto3.client('batch')
COST_EXPLORER = boto3.client('ce')


def get_time_period(today: date) -> dict:
    start = today.replace(day=1)
    end = start + dateutil.relativedelta.relativedelta(months=1)
    return {'Start': str(start), 'End': str(end)}


def get_month_to_date_spending(today: date) -> float:
    time_period = get_time_period(today)
    granularity = 'MONTHLY'
    metrics = ['UnblendedCost']
    response = COST_EXPLORER.get_cost_and_usage(TimePeriod=time_period, Granularity=granularity, Metrics=metrics)
    return float(response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])


def get_current_desired_vcpus(compute_environment_arn):
    response = BATCH.describe_compute_environments(computeEnvironments=[compute_environment_arn])
    return response['computeEnvironments'][0]['computeResources']['desiredvCpus']


def set_max_vcpus(compute_environment_arn: str, target_max_vcpus: int, current_desired_vcpus: int) -> None:
    if current_desired_vcpus <= target_max_vcpus:
        compute_resources = {'maxvCpus': target_max_vcpus}
        print(f'Updating {compute_environment_arn} compute resources to {compute_resources}')
        BATCH.update_compute_environment(
            computeEnvironment=compute_environment_arn,
            computeResources=compute_resources,
            state='ENABLED',
        )
    else:
        print(
            f'Disabling {compute_environment_arn}. Current desiredvCpus {current_desired_vcpus} is larger than '
            f'target maxvCpus {target_max_vcpus}'
        )
        BATCH.update_compute_environment(
            computeEnvironment=compute_environment_arn,
            state='DISABLED',
        )


def get_target_max_vcpus(
    today, monthly_budget, month_to_date_spending, default_max_vcpus, expanded_max_vcpus, required_surplus
):
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    month_to_date_budget = monthly_budget * today.day / days_in_month
    available_surplus = month_to_date_budget - month_to_date_spending

    print(f'Month-to-date budget: ${month_to_date_budget:,.2f}')
    print(f'Month-to-date spending: ${month_to_date_spending:,.2f}')
    print(f'Available surplus: ${available_surplus:,.2f}')
    print(f'Required surplus: ${required_surplus:,.2f}')

    if available_surplus < required_surplus:
        max_vcpus = default_max_vcpus
    else:
        max_vcpus = expanded_max_vcpus
    return max_vcpus


def lambda_handler(event, context):
    target_max_vcpus = get_target_max_vcpus(
        today=date.today(),
        monthly_budget=int(environ['MONTHLY_BUDGET']),
        month_to_date_spending=get_month_to_date_spending(date.today()),
        default_max_vcpus=int(environ['DEFAULT_MAX_VCPUS']),
        expanded_max_vcpus=int(environ['EXPANDED_MAX_VCPUS']),
        required_surplus=int(environ['REQUIRED_SURPLUS']),
    )
    current_desired_vcpus = get_current_desired_vcpus(environ['COMPUTE_ENVIRONMENT_ARN'])
    set_max_vcpus(
        compute_environment_arn=environ['COMPUTE_ENVIRONMENT_ARN'],
        target_max_vcpus=target_max_vcpus,
        current_desired_vcpus=current_desired_vcpus,
    )
