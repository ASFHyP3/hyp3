from os import environ
from pathlib import Path

from flask import make_response, jsonify, redirect, request, g, abort, Response
from flask_cors import CORS
from openapi_core.contrib.flask.views import FlaskOpenAPIView

from hyp3_api import app, handlers, auth
from hyp3_api.openapi import get_spec

api_spec_file = Path(__file__).parent / 'api-spec' / 'openapi-spec.yml'
api_spec = get_spec(api_spec_file)
CORS(app, origins=r'https?://([-\w]+\.)*asf\.alaska\.edu', supports_credentials=True)

AUTHENTICATED_ROUTES = ['/jobs', '/user']


@app.before_request
def check_system_available():
    if environ['SYSTEM_AVAILABLE'] != "true":
        message = 'HyP3 is currently unavailable. Please try again later.'
        error = {
            'detail': message,
            'status': 503,
            'title': 'Service Unavailable',
            'type': 'about:blank'
        }
        return make_response(jsonify(error), 503)


@app.before_request
def authenticate_user():
    cookie = request.cookies.get('asf-urs')
    auth_info = auth.decode_token(cookie)
    if auth_info is not None:
        g.user = auth_info['sub']
    else:
        if request.path in AUTHENTICATED_ROUTES and request.method != 'OPTIONS':
            abort(handlers.error(401, 'Unauthorized', 'No authorization token provided'))


@app.route('/')
def redirect_to_ui():
    return redirect('/ui')


@app.errorhandler(404)
def error404(e):
    return handlers.error(404, 'Not Found',
                          'The requested URL was not found on the server.'
                          ' If you entered the URL manually please check your spelling and try again.')

class Jobs(FlaskOpenAPIView):
    def post(self):
        return jsonify(handlers.post_jobs(request.get_json(), g.user))

    def get(self, job_id):
        if job_id is not None:
            return jsonify(handlers.get_job_by_id(job_id))
        parameters = request.openapi.parameters.query
        start = parameters.get('start')
        end = parameters.get('end')
        return jsonify(handlers.get_jobs(
            g.user,
            start.isoformat(timespec='seconds') if start else None,
            end.isoformat(timespec='seconds') if end else None,
            parameters.get('status_code'),
            parameters.get('name'),
            parameters.get('job_type'),
            parameters.get('start_token')
        ))


class User(FlaskOpenAPIView):
    def get(self):
        return jsonify(handlers.get_user(g.user))


app.json_encoder = handlers.DecimalEncoder

jobs_view = Jobs.as_view('jobs', api_spec)
app.add_url_rule('/jobs', view_func=jobs_view, methods=['GET'], defaults={'job_id': None})
app.add_url_rule('/jobs', view_func=jobs_view, methods=['POST'])
app.add_url_rule('/jobs/<job_id>', view_func=jobs_view, methods=['GET'])

user_view = User.as_view('user', api_spec)
app.add_url_rule('/user', view_func=user_view)
