import lambda_handler
from flask_api import status


def test_404_response():
    event = {
        'path': '/',
        'httpMethod': 'GET',
        'body': '',
        'headers': {},
        'requestContext': {},
    }
    response = lambda_handler.handler(event, None)
    assert response['statusCode'] == status.HTTP_404_NOT_FOUND
    assert response['headers']['Content-Type'] == 'application/problem+json'
    assert response['isBase64Encoded'] == False


def test_401_response():
    event = {
        'path': '/jobs',
        'httpMethod': 'POST',
        'body': '',
        'headers': {},
        'requestContext': {},
    }
    response = lambda_handler.handler(event, None)
    assert response['statusCode'] == status.HTTP_401_UNAUTHORIZED
    assert response['headers']['Content-Type'] == 'application/problem+json'
    assert response['isBase64Encoded'] is False
