import json
import re
from os import environ, path

import pytest
import responses
import yaml
from moto import mock_dynamodb2

from hyp3_api import CMR_URL, DYNAMODB_RESOURCE, auth, connexion_app  # noqa hyp3 must be imported here

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
def table():
    table_properties = get_table_properties_from_template()
    with mock_dynamodb2():
        table = DYNAMODB_RESOURCE.create_table(
            TableName=environ['TABLE_NAME'],
            **table_properties,
        )
        yield table


def get_table_properties_from_template():
    yaml.SafeLoader.add_multi_constructor('!', lambda loader, suffix, node: None)
    template_file = path.join(path.dirname(__file__), '../../cloudformation.yml')
    with open(template_file, 'r') as f:
        template = yaml.safe_load(f)
    table_properties = template['Resources']['JobsTable']['Properties']
    return table_properties


def make_job(granule='S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38',
             description='someDescription',
             name='someName',
             job_type='RTC_GAMMA'):
    job = {
        'job_type': job_type,
        'job_parameters': {
            'granule': granule
        }
    }
    if description is not None:
        job['description'] = description
    if name is not None:
        job['name'] = name

    return job


def submit_batch(client, batch=None):
    if batch is None:
        batch = [make_job()]
    return client.post(JOBS_URI, json={'jobs': batch})


def make_db_record(job_id,
                   granule='S1A_IW_SLC__1SDV_20200610T173646_20200610T173704_032958_03D14C_5F2B',
                   job_type='RTC_GAMMA',
                   user_id=DEFAULT_USERNAME,
                   name=None,
                   request_time='2019-12-31T15:00:00+00:00',
                   status_code='RUNNING',
                   expiration_time='2019-12-31T15:00:00+00:00',
                   files=None,
                   browse_images=None,
                   thumbnail_images=None):
    record = {
        'job_id': job_id,
        'user_id': user_id,
        'job_type': job_type,
        'job_parameters': {
            'granule': granule,
        },
        'request_time': request_time,
        'status_code': status_code,
    }
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
    granules = [job['job_parameters']['granule'] for job in batch]
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


def login(client, username=DEFAULT_USERNAME):
    client.set_cookie('localhost', AUTH_COOKIE, auth.get_mock_jwt_cookie(username))
