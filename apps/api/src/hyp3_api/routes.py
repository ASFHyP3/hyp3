from os import environ
from pathlib import Path

from flask import make_response, jsonify, redirect, request, g, abort
from flask_cors import CORS
from openapi_core.contrib.flask.views import FlaskOpenAPIView


from hyp3_api import app, handlers, auth
from hyp3_api.openapi import get_spec


api_spec_file = Path(__file__).parent / 'api-spec' / 'openapi-spec.yml'
api_spec = get_spec(api_spec_file)
CORS(app, origins=r'https?://([-\w]+\.)*asf\.alaska\.edu', supports_credentials=True)


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
    auth_info =  auth.decode_token(cookie)
    if auth_info is not None:
        g.user = auth_info['sub']
    else:
        abort(401)


@app.route('/')
def redirect_to_ui():
    return redirect('/ui')


class Jobs(FlaskOpenAPIView):
    def post(self):
        return jsonify(handlers.post_jobs(request.get_json(), g.user))

    def get(self):
        parameters = request.openapi.parameters.query
        return jsonify(handlers.get_jobs(
            g.user,
            parameters.get('start'),
            parameters.get('end'),
            parameters.get('status_code'),
            parameters.get('name'),
            parameters.get('job_type'),
            parameters.get('start_token')
        ))


app.add_url_rule('/jobs', view_func=Jobs.as_view('jobs', api_spec))
