from http import HTTPStatus

import pytest

from test_api.conftest import JOBS_URI, login


@pytest.mark.network
def test_submit_opera_rtc_s1_validate_only(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'validate_only': True,
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {'granules': ['S1_118338_IW2_20170102T124017_VV_0675-BURST']},
                }
            ],
        },
    )
    assert response.status_code == HTTPStatus.OK
    jobs = tables.jobs_table.scan()['Items']
    assert len(jobs) == 0


# TODO: more tests
