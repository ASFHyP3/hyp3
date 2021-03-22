import json
import re
from os import environ, path

import pytest
import responses
import yaml
from moto import mock_dynamodb2

from hyp3_api import CMR_URL, DYNAMODB_RESOURCE, auth, connexion_app
from hyp3_api.util import get_granules

AUTH_COOKIE = 'asf-urs'
JOBS_URI = '/jobs'
USER_URI = '/user'

DEFAULT_JOB_ID = 'myJobId'
DEFAULT_USERNAME = 'test_username'

CMR_URL_RE = re.compile(f'{CMR_URL}.*')


@pytest.fixture
def client():
    with connexion_app.app.test_client() as test_client:
        yield test_client


@pytest.fixture
def tables():
    with mock_dynamodb2():
        jobs_table = DYNAMODB_RESOURCE.create_table(
            TableName=environ['JOBS_TABLE_NAME'],
            **get_table_properties_from_template('JobsTable'),
        )
        users_table = DYNAMODB_RESOURCE.create_table(
            TableName=environ['USERS_TABLE_NAME'],
            **get_table_properties_from_template('UsersTable'),
        )
        yield {'users_table': users_table, 'jobs_table': jobs_table}


def get_table_properties_from_template(resource_name):
    yaml.SafeLoader.add_multi_constructor('!', lambda loader, suffix, node: None)
    template_file = path.join(path.dirname(__file__), '../../apps/main-cf.yml')
    with open(template_file, 'r') as f:
        template = yaml.safe_load(f)
    table_properties = template['Resources'][resource_name]['Properties']
    return table_properties


def make_job(granules=['S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38'],
             name='someName',
             job_type='RTC_GAMMA',
             parameters={},):
    job = {
        'job_type': job_type,
        'job_parameters': {
            'granules': granules,
            **parameters
        }
    }
    if name is not None:
        job['name'] = name

    return job


def submit_batch(client, batch=None, validate_only=None):
    if batch is None:
        batch = [make_job()]
    payload = {
        'jobs': batch,
    }
    if validate_only is not None:
        payload['validate_only'] = validate_only
    return client.post(JOBS_URI, json=payload)


def make_db_record(job_id,
                   granules=['S1A_IW_SLC__1SDV_20200610T173646_20200610T173704_032958_03D14C_5F2B'],
                   job_type='RTC_GAMMA',
                   user_id=DEFAULT_USERNAME,
                   request_time='2019-12-31T15:00:00+00:00',
                   status_code='RUNNING',
                   expiration_time='2019-12-31T15:00:00+00:00',
                   name=None,
                   files=None,
                   browse_images=None,
                   thumbnail_images=None):
    record = {
        'job_id': job_id,
        'user_id': user_id,
        'job_type': job_type,
        'job_parameters': {
            'granules': granules,
        },
        'request_time': request_time,
        'status_code': status_code,
    }
    if name is not None:
        record['name'] = name
    if files is not None:
        record['files'] = files
    if browse_images is not None:
        record['browse_images'] = browse_images
    if thumbnail_images is not None:
        record['thumbnail_images'] = thumbnail_images
    if expiration_time is not None:
        record['expiration_time'] = expiration_time
    return record


def setup_requests_mock(batch):
    granules = get_granules(batch)
    cmr_response = {
        'feed': {
            'entry': [
                {
                    'producer_granule_id': granule,
                    'polygons': [
                        ['3.871941 -157.47052 62.278873 -156.62677 62.712959 -151.784653 64.318275 -152.353271 '
                         '63.871941 -157.47052']
                    ],
                } for granule in granules
            ]
        }
    }
    responses.reset()
    responses.add(responses.POST, CMR_URL_RE, json.dumps(cmr_response))


def sort_by_request_time(batch):
    return sorted(batch, key=lambda k: k['request_time'], reverse=True)


def login(client, username=DEFAULT_USERNAME):
    client.set_cookie('localhost', AUTH_COOKIE, auth.get_mock_jwt_cookie(username))


def list_have_same_elements(l1, l2):
    return [item for item in l1 if item not in l2] == [] == [item for item in l2 if item not in l1]
