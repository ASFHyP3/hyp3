from flask_api import status

from hyp3_api import lambda_handler


def test_404_response():
    event = {
        'version': '2.0',
        'rawPath': '/foo',
        'headers': {},
        'requestContext': {
            'http': {
                'method': 'GET',
            },
        },
    }
    response = lambda_handler.handler(event, None)
    assert response['statusCode'] == status.HTTP_404_NOT_FOUND
    assert response['headers']['Content-Type'] == 'application/problem+json'
    assert response['isBase64Encoded'] is False


def test_401_response():
    event = {
        'version': '2.0',
        'rawPath': '/jobs',
        'headers': {},
        'requestContext': {
            'http': {
                'method': 'POST',
            },
        },
    }
    response = lambda_handler.handler(event, None)
    assert response['statusCode'] == status.HTTP_401_UNAUTHORIZED
    assert response['headers']['Content-Type'] == 'application/problem+json'
    assert response['isBase64Encoded'] is False
