import datetime
import json
from collections.abc import Iterable
from decimal import Decimal
from os import environ
from pathlib import Path

import werkzeug
import yaml
from flask import Response, abort, g, jsonify, make_response, redirect, render_template, request
from flask.json.provider import JSONProvider
from flask_cors import CORS
from openapi_core import OpenAPI
from openapi_core.contrib.flask.decorators import FlaskOpenAPIViewDecorator
from openapi_core.contrib.flask.handlers import FlaskOpenAPIErrorsHandler

import dynamo
from hyp3_api import app, auth, handlers
from hyp3_api.openapi import get_spec_yaml


api_spec_file = Path(__file__).parent / 'api-spec' / 'openapi-spec.yml'
api_spec_dict = get_spec_yaml(api_spec_file)
api_spec = OpenAPI.from_dict(api_spec_dict)
CORS(app, origins=r'https?://([-\w]+\.)*asf\.alaska\.edu', supports_credentials=True)

AUTHENTICATED_ROUTES = ['/jobs', '/user']


@app.before_request
def check_system_available() -> Response | None:
    if environ['SYSTEM_AVAILABLE'] != 'true':
        message = 'HyP3 is currently unavailable. Please try again later.'
        error = {'detail': message, 'status': 503, 'title': 'Service Unavailable', 'type': 'about:blank'}
        return make_response(jsonify(error), 503)
    return None


@app.before_request
def authenticate_user() -> None:
    token = None
    payload = None
    if request.authorization.type == 'Bearer':
        token = request.authorization.token
        payload = auth.decode_token(token)

    if payload is not None:
        g.user = payload['uid']
        g.edl_access_token = token
    else:
        if any([request.path.startswith(route) for route in AUTHENTICATED_ROUTES]) and request.method != 'OPTIONS':
            abort(handlers.problem_format(401, 'No authorization token provided'))


@app.route('/')
def redirect_to_ui() -> werkzeug.wrappers.response.Response:
    return redirect('/ui/')


@app.route('/openapi.json')
def get_open_api_json() -> Response:
    return jsonify(api_spec_dict)


@app.route('/openapi.yaml')
def get_open_api_yaml() -> str:
    return yaml.dump(api_spec_dict)


@app.route('/ui/')
def render_ui() -> str:
    return render_template('index.html')


@app.errorhandler(404)
def error404(_) -> Response:
    return handlers.problem_format(
        404,
        'The requested URL was not found on the server.'
        ' If you entered the URL manually please check your spelling and try again.',
    )


class CustomEncoder(json.JSONEncoder):
    def default(self, o: object) -> object:
        # https://docs.python.org/3/library/json.html#json.JSONEncoder.default

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

        # Let the base class default method raise the TypeError
        return super().default(o)


class CustomJSONProvider(JSONProvider):
    def dumps(self, obj: object, **kwargs: object) -> str:
        return json.dumps(obj, cls=CustomEncoder)

    def loads(self, s: str | bytes, **kwargs: object) -> object:
        return json.loads(s)


class ErrorHandler(FlaskOpenAPIErrorsHandler):
    def __init__(self) -> None:
        super().__init__()

    def __call__(self, errors: Iterable[Exception]) -> Response:
        response = super().__call__(errors)
        error = response.json['errors'][0]  # type: ignore[index]
        return handlers.problem_format(error['status'], error['title'])


app.json = CustomJSONProvider(app)

openapi = FlaskOpenAPIViewDecorator(
    api_spec,
    response_cls=None,  # type: ignore[arg-type]
    errors_handler_cls=ErrorHandler,
)


@app.route('/costs', methods=['GET'])
def costs_get() -> Response:
    return jsonify(dynamo.jobs.COSTS)


@app.route('/jobs', methods=['POST'])
@openapi
def jobs_post() -> Response:
    return jsonify(handlers.post_jobs(request.get_json(), g.user))


@app.route('/jobs', methods=['GET'])
@openapi
def jobs_get() -> Response:
    parameters = request.openapi.parameters.query  # type: ignore[attr-defined]
    start = parameters.get('start')
    end = parameters.get('end')
    return jsonify(
        handlers.get_jobs(
            parameters.get('user_id') or g.user,
            start.isoformat(timespec='seconds') if start else None,
            end.isoformat(timespec='seconds') if end else None,
            parameters.get('status_code'),
            parameters.get('name'),
            parameters.get('job_type'),
            parameters.get('start_token'),
        )
    )


@app.route('/jobs/<job_id>', methods=['GET'])
@openapi
def jobs_get_by_job_id(job_id: str) -> Response:
    return jsonify(handlers.get_job_by_id(job_id))


@app.route('/jobs/<job_id>', methods=['PATCH'])
@openapi
def jobs_patch_by_job_id(job_id: str) -> Response:
    return jsonify(handlers.patch_job_by_id(request.get_json(), job_id, g.user))


@app.route('/user', methods=['PATCH'])
@openapi
def user_patch() -> Response:
    return jsonify(handlers.patch_user(request.get_json(), g.user, g.edl_access_token))


@app.route('/user', methods=['GET'])
@openapi
def user_get() -> Response:
    return jsonify(handlers.get_user(g.user))
