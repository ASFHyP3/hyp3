import json
import re

import pytest
import responses

from hyp3_api import CMR_URL, app, auth
from hyp3_api.util import get_granules

AUTH_COOKIE = 'asf-urs'
JOBS_URI = '/jobs'
USER_URI = '/user'
SUBSCRIPTIONS_URI = '/subscriptions'

DEFAULT_JOB_ID = 'myJobId'
DEFAULT_USERNAME = 'test_username'

CMR_URL_RE = re.compile(f'{CMR_URL}.*')


@pytest.fixture
def client():
    with app.test_client() as test_client:
        yield test_client


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
                   subscription_id=None,
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
    if subscription_id is not None:
        record['subscription_id'] = subscription_id
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


def login(client, username=DEFAULT_USERNAME):
    client.set_cookie('localhost', AUTH_COOKIE, auth.get_mock_jwt_cookie(username))


def assert_status(response, status):
    try:
        assert response.status_code == status
    except AssertionError:
        raise AssertionError(str(response.data))
