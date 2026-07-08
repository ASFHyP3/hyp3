import datetime
import json
from collections.abc import Iterable
from decimal import Decimal
from os import environ
from pathlib import Path

import werkzeug
import yaml
from flask import Request, Response, abort, g, jsonify, make_response, redirect, render_template, request
from flask.json.provider import JSONProvider
from flask_cors import CORS
from jsonschema import Draft7Validator
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


JWKS_CLIENT = auth.get_jwks_client()
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
    if any([request.path.startswith(route) for route in AUTHENTICATED_ROUTES]) and request.method != 'OPTIONS':
        try:
            if request.authorization and request.authorization.type == 'bearer':
                g.user, g.edl_access_token = auth.decode_edl_bearer_token(str(request.authorization.token), JWKS_CLIENT)
            elif 'asf-urs' in request.cookies:
                g.user, g.edl_access_token = auth.decode_asf_cookie(request.cookies['asf-urs'])
            else:
                abort(handlers.problem_format(401, 'No authorization token provided'))
        except auth.InvalidTokenException as e:
            abort(handlers.problem_format(401, str(e)))


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


def validate_files(request: Request) -> None:
    job_type = request.form['job_type']
    job_spec_path = Path(f'job_spec/{job_type}.yml')

    with Path.open(job_spec_path) as file:
        job_spec = yaml.safe_load(file)

    file_spec = job_spec[job_type]['files']
    request_files = dict(request.files)

    # Check that all required files have been uploaded
    missing_files = []
    for key in file_spec.keys():
        if 'required' in file_spec[key].keys() and file_spec[key]['required']:
            if key not in request_files.keys():
                missing_files.append(key)

    if len(missing_files) > 0:
        abort(handlers.problem_format(400, f'Missing required file(s): {", ".join(missing_files)}'))

    # Check that only the files for the current job type have been provided
    for file_param in request.files.keys():
        if file_param not in file_spec.keys():
            abort(
                handlers.problem_format(
                    400, f'Invalid file provided: {file_param}: {request.files[file_param].filename}'
                )
            )

    # Check that the filetype is correct
    for param, file_obj in request.files.items():
        filetype = file_obj.mimetype
        allowed_types = file_spec[param]['allowed_types']
        if filetype not in allowed_types:
            abort(
                handlers.problem_format(
                    400, f"Invalid file type for {param}, '{filetype}' is not one of {allowed_types}."
                )
            )


def validate_job_parameters(request_dict: dict) -> None:
    job_parameters_list = api_spec_dict['components']['schemas']['job']['properties']['job_parameters']['anyOf']
    job_type = request_dict['job_type']

    # TODO: There is probably a better way of doing this filtering.
    job_parameter_schema = None
    for job_parameters in job_parameters_list:
        if f' {job_type} ' in job_parameters['description']:
            job_parameter_schema = job_parameters
            break

    validator = Draft7Validator(job_parameter_schema)  # type: ignore
    errors = sorted(validator.iter_errors(request_dict['job_parameters']), key=lambda e: e.path)

    if errors:
        abort(handlers.problem_format(400, str(errors[0])))


def get_request_dict(request: Request) -> dict:
    request_form = dict(request.form)
    allowed_params = ['job_type', 'name', 'bucket', 'bucket_prefix', 'job_parameters']

    # Ensure that unused file params are removed from the request
    params = list(request_form.keys())
    for param in params:
        if param not in allowed_params:
            request_form.pop(param)

    request_form['job_parameters'] = json.loads(request_form['job_parameters'])

    for param, file_obj in request.files.items():
        request_form['job_parameters'][param] = file_obj.filename  # type: ignore[index]

    return request_form


@app.route('/upload-job', methods=['POST'])
@openapi
def upload_job_post() -> Response:
    request_dict = get_request_dict(request)

    validate_files(request)
    validate_job_parameters(request_dict)

    return handlers.post_upload_job(request_dict, request.files, g.user)


@app.route('/jobs', methods=['POST'])
@openapi
def jobs_post() -> Response:
    return jsonify(handlers.post_jobs(request.get_json(), g.user))


@app.route('/jobs', methods=['PATCH'])
@openapi
def jobs_patch() -> Response:
    handlers.patch_jobs(request.get_json(), g.user)
    return jsonify({})


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


@app.route('/bucket-policy/<bucket_name>', methods=['GET'])
@openapi
def bucket_policy_get(bucket_name: str) -> Response:
    return jsonify(handlers.get_bucket_policy(bucket_name))
