from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
import responses

import hyp3_api.validation
from test_api.conftest import JOBS_URI, login


@pytest.mark.network
def test_aria_s1_gunw_job(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'ARIA_S1_GUNW',
                    'job_parameters': {'reference_date': '2022-01-01', 'secondary_date': '2022-01-02', 'frame_id': 1}
                }
            ],
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert len(tables.jobs_table.scan()['Items']) == 1


@pytest.mark.network
def test_aria_job_with_bad_date(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'ARIA_S1_GUNW',
                    'job_parameters': {'reference_date': '2014-06-14', 'secondary_date': '2022-01-02', 'frame_id': 100}
                }
            ],
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'is before the start of the sentinel 1 mission' in response.json['detail']
    assert len(tables.jobs_table.scan()['Items']) == 0
