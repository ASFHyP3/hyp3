import datetime
import json
from decimal import Decimal
from os import environ
from pathlib import Path

import shapely.errors
import shapely.wkt
import yaml
from flask import abort, g, jsonify, make_response, redirect, render_template, request
from flask_cors import CORS
from openapi_core.contrib.flask.handlers import FlaskOpenAPIErrorsHandler
from openapi_core.contrib.flask.views import FlaskOpenAPIView
from openapi_core.spec.shortcuts import create_spec
from openapi_core.validation.request.validators import RequestValidator
from openapi_core.validation.response.datatypes import ResponseValidationResult
from openapi_core.unmarshalling.schemas.factories import SchemaUnmarshallersFactory
from openapi_schema_validator import OAS30Validator
from openapi_core.unmarshalling.schemas.formatters import Formatter

from hyp3_api import app, auth, handlers
from hyp3_api.openapi import get_spec_yaml

api_spec_file = Path(__file__).parent / 'api-spec' / 'openapi-spec.yml'
api_spec_dict = get_spec_yaml(api_spec_file)
api_spec = create_spec(api_spec_dict)
CORS(app, origins=r'https?://([-\w]+\.)*asf\.alaska\.edu', supports_credentials=True)

AUTHENTICATED_ROUTES = ['/jobs', '/user', '/subscriptions']


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
        if any([request.path.startswith(route) for route in AUTHENTICATED_ROUTES]) and request.method != 'OPTIONS':
            abort(handlers.problem_format(401, 'No authorization token provided'))


@app.route('/')
def redirect_to_ui():
    return redirect('/ui/')


@app.route('/openapi.json')
def get_open_api_json():
    return jsonify(api_spec_dict)


@app.route('/openapi.yaml')
def get_open_api_yaml():
    return yaml.dump(api_spec_dict)


@app.route('/ui/')
def render_ui():
    return render_template('index.html')


@app.errorhandler(404)
def error404(e):
    return handlers.problem_format(404, 'The requested URL was not found on the server.'
                                        ' If you entered the URL manually please check your spelling and try again.')


class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            if o.tzinfo:
                # eg: '2015-09-25T23:14:42.588601+00:00'
                return o.isoformat('T')
            else:
                # No timezone present - assume UTC.
                # eg: '2015-09-25T23:14:42.588601Z'
                return o.isoformat('T') + 'Z'

        if isinstance(o, datetime.date):
            return o.isoformat()
        if isinstance(o, Decimal):
            if o == int(o):
                return int(o)
            return float(o)
        json.JSONEncoder.default(self, o)


class NonValidator:
    def __init__(self, spec):
        pass

    def validate(self, res):
        return ResponseValidationResult()


class WktFormatter(Formatter):
    def validate(self, value) -> bool:
        try:
            shapely.wkt.loads(value)
        except shapely.errors.WKTReadingError:
            return False
        return True


class ErrorHandler(FlaskOpenAPIErrorsHandler):
    def __init__(self):
        super().__init__()

    @classmethod
    def handle(cls, errors):
        response = super().handle(errors)
        error = response.json['errors'][0]
        return handlers.problem_format(error['status'], error['title'])


class Jobs(FlaskOpenAPIView):
    def __init__(self, spec):
        super().__init__(spec)
        self.response_validator = NonValidator
        self.openapi_errors_handler = ErrorHandler

    def post(self):
        return jsonify(handlers.post_jobs(request.get_json(), g.user))

    def get(self, job_id):
        if job_id is not None:
            return jsonify(handlers.get_job_by_id(job_id))
        parameters = request.openapi.parameters.query
        start = parameters.get('start')
        end = parameters.get('end')
        subscription_id = parameters.get('subscription_id')
        if subscription_id is not None:
            subscription_id = str(subscription_id)
        return jsonify(handlers.get_jobs(
            g.user,
            start.isoformat(timespec='seconds') if start else None,
            end.isoformat(timespec='seconds') if end else None,
            parameters.get('status_code'),
            parameters.get('name'),
            parameters.get('job_type'),
            parameters.get('start_token'),
            subscription_id,
        ))


class User(FlaskOpenAPIView):
    def __init__(self, spec):
        super().__init__(spec)
        self.response_validator = NonValidator
        self.openapi_errors_handler = ErrorHandler

    def get(self):
        return jsonify(handlers.get_user(g.user))


class Subscriptions(FlaskOpenAPIView):
    def __init__(self, spec):
        super().__init__(spec)

        schema_unmarshallers_factory = SchemaUnmarshallersFactory(
            OAS30Validator,
            custom_formatters={'wkt': WktFormatter()},
        )
        self.request_validator = RequestValidator(schema_unmarshallers_factory)
        self.response_validator = NonValidator
        self.openapi_errors_handler = ErrorHandler

    def post(self):
        body = request.get_json()
        return jsonify(handlers.post_subscriptions(body, g.user))

    def get(self, subscription_id):
        if subscription_id is not None:
            return jsonify(handlers.get_subscription_by_id(subscription_id))
        parameters = request.openapi.parameters.query
        return jsonify(handlers.get_subscriptions(
            g.user,
            parameters.get('name'),
            parameters.get('job_type'),
            parameters.get('enabled'),
        ))

    def patch(self, subscription_id):
        body = request.get_json()
        return jsonify(handlers.patch_subscriptions(subscription_id, body, g.user))


app.json_encoder = CustomEncoder

jobs_view = Jobs.as_view('jobs', api_spec)
app.add_url_rule('/jobs', view_func=jobs_view, methods=['GET'], defaults={'job_id': None})
app.add_url_rule('/jobs', view_func=jobs_view, methods=['POST'])
app.add_url_rule('/jobs/<job_id>', view_func=jobs_view, methods=['GET'])

user_view = User.as_view('user', api_spec)
app.add_url_rule('/user', view_func=user_view)

subscriptions_view = Subscriptions.as_view('subscriptions', api_spec)
app.add_url_rule('/subscriptions/<subscription_id>', view_func=subscriptions_view, methods=['PATCH', 'GET'])
app.add_url_rule('/subscriptions', view_func=subscriptions_view, methods=['GET'], defaults={'subscription_id': None})
app.add_url_rule('/subscriptions', view_func=subscriptions_view, methods=['POST'])
