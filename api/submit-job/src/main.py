import json
from os import environ
from http.cookies import SimpleCookie
from urllib.parse import urljoin, quote_plus

import boto3
import jwt

BATCH_CLIENT = boto3.client('batch')


def redirect_response(url):
    return {
        'statusCode': 307,
        'headers': {
            'Location': url,
        },
    }


def is_logged_in(headers):
    if not headers:
        return False

    if not headers.get('Cookie'):
        return False

    cookie = SimpleCookie(headers['Cookie'])
    if not cookie.get(environ['AUTH_COOKIE_NAME']):
        return False

    token = cookie[environ['AUTH_COOKIE_NAME']].value
    try:
        jwt.decode(token, environ['AUTH_PUBLIC_KEY'])
    except (jwt.DecodeError, jwt.ExpiredSignatureError):
        return False

    return True


def get_redirect_url(event):
    invoked_url = urljoin('https://' + environ['DOMAIN_NAME'], event['requestContext']['path'])
    redirect_url = environ['AUTH_URL'] + '&state=' + quote_plus(invoked_url)
    if not event['headers'].get('User-Agent', '').startswith('Mozilla'):
        redirect_url += '&app_type=401'
    return redirect_url


def lambda_handler(event, context):
    if not is_logged_in(event.get('headers')):
        redirect_url = get_redirect_url(event)
        return redirect_response(redirect_url)

    parameters = json.loads(event['body'])
    job = BATCH_CLIENT.submit_job(
        jobName=parameters['granule'],
        jobQueue=environ['JOB_QUEUE'],
        jobDefinition=environ['JOB_DEFINITION'],
        parameters=parameters
    )
    response_body = {
        'jobId': job['jobId'],
        'jobName': job['jobName']
    }
    return {
        'statusCode': 200,
        'body': json.dumps(response_body)
    }
