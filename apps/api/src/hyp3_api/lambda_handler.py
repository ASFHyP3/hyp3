import serverless_wsgi

from hyp3_api import app


serverless_wsgi.TEXT_MIME_TYPES.append('application/problem+json')


def handler(event, context):
    response = serverless_wsgi.handle_request(app, event, context)
    print(response)
    return response
