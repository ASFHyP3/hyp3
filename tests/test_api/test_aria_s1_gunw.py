from http import HTTPStatus

import pytest

from test_api.conftest import FUTURE_DATE, JOBS_URI, login


@pytest.mark.network
def test_aria_s1_gunw_job(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'ARIA_S1_GUNW',
                    'job_parameters': {'reference_date': '2022-01-02', 'secondary_date': '2022-01-01', 'frame_id': 1},
                }
            ],
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert len(tables.jobs_table.scan()['Items']) == 1


@pytest.mark.parametrize(
    'job_parameters',
    [
        ({'reference_date': 'foo', 'secondary_date': '2022-01-01', 'frame_id': 1}),
        ({'reference_date': '2022-01-01', 'secondary_date': 'bar', 'frame_id': 1}),
        ({'reference_date': '2022-01-02', 'secondary_date': '2022-01-01', 'frame_id': 'foo'}),
    ],
)
def test_aria_s1_gunw_job_schema(client, tables, approved_user, job_parameters):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [{'job_type': 'ARIA_S1_GUNW', 'job_parameters': job_parameters}],
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'is not valid under any of the given schemas' in response.json['detail']
    assert len(tables.jobs_table.scan()['Items']) == 0


@pytest.mark.network
@pytest.mark.parametrize(
    'job_parameters,error_message',
    [
        (
            {'reference_date': '2014-06-14', 'secondary_date': '2022-01-02', 'frame_id': 100},
            'is before the start of the sentinel 1 mission',
        ),
        ({'reference_date': FUTURE_DATE, 'secondary_date': '2021-01-01', 'frame_id': 1}, 'is a date in the future'),
        (
            {'reference_date': '2021-01-01', 'secondary_date': '2021-01-02', 'frame_id': 1},
            'secondary date must be earlier than reference date',
        ),
    ],
)
def test_aria_job_error_messages(client, tables, approved_user, job_parameters, error_message):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'ARIA_S1_GUNW',
                    'job_parameters': job_parameters,
                }
            ],
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert error_message in response.json['detail']
    assert len(tables.jobs_table.scan()['Items']) == 0
