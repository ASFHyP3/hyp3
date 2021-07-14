from os import environ

import asf_search
import boto3

DB = boto3.resource('dynamodb')


def handle_subscription(subscription):

    pass


def get_subscriptions():
    return []


def lambda_handler(event, contect):
    subscriptions = get_subscriptions()
    for subscription in subscriptions:
        handle_subscription(subscription)