from http import HTTPStatus

import pytest

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
                    'job_parameters': {
                        'reference': [
                            "S1A_IW_SLC__1SDV_20250308T020834_20250308T020900_058207_073136_ECE5",
                            "S1A_IW_SLC__1SDV_20250308T020858_20250308T020926_058207_073136_3B06",
                        ],
                        'secondary': [
                            "S1A_IW_SLC__1SDV_20250212T020834_20250212T020900_057857_0722EF_6432",
                            "S1A_IW_SLC__1SDV_20250212T020858_20250212T020926_057857_0722EF_B232"
                        ]
                    }
                }
            ],
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert len(tables.jobs_table.scan()['Items']) == 1


@pytest.mark.parametrize(
    'job_parameters',
    [
        ({'reference': 'foo', 'secondary': [
            "S1A_IW_SLC__1SDV_20250212T020834_20250212T020900_057857_0722EF_6432",
            "S1A_IW_SLC__1SDV_20250212T020858_20250212T020926_057857_0722EF_B232"
        ], 'frame_id': 1}),
        ({'reference': [
            "S1A_IW_SLC__1SDV_20250308T020834_20250308T020900_058207_073136_ECE5",
            "S1A_IW_SLC__1SDV_20250308T020858_20250308T020926_058207_073136_3B06",
        ], 'secondary': 'bar', 'frame_id': 1}),
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
            {
                'reference': [
                    "S1A_IW_SLC__1SDV_20250308T020834_20250308T020900_058207_073136_ECE5",
                    "S1A_IW_SLC__1SDV_20250308T021358_20250308T020926_058207_073136_3B06",
                ],
                'secondary': [
                    "S1A_IW_SLC__1SDV_20250212T020834_20250212T020900_057857_0722EF_6432",
                    "S1A_IW_SLC__1SDV_20250212T020858_20250212T020926_057857_0722EF_B232"
                ],
                'frame_id': 100
            },
            r'scenes in reference list are too far apart in time.',
        ),
        (
            {
                'reference': [
                    "S1A_IW_SLC__1SDV_20250308T020834_20250308T020900_058207_073136_ECE5",
                    "S1A_IW_SLC__1SDV_20250308T020858_20250308T020926_058207_073136_3B06",
                ],
                'secondary': [
                    "S1A_IW_SLC__1SDV_20250212T020834_20250212T020900_057857_0722EF_6432",
                    "S1A_IW_SLC__1SDV_20250212T021358_20250212T020926_057857_0722EF_B232"
                ],
                'frame_id': 100
            },
            r'scenes in secondary list are too far apart in time.',
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
