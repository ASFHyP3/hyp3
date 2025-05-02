from http import HTTPStatus
from unittest.mock import MagicMock

import pytest

import hyp3_api.validation
from test_api.conftest import JOBS_URI, login


@pytest.mark.network
def test_opera_rtc_s1_vv(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {'granules': ['S1_118338_IW2_20170102T124017_VV_0675-BURST']},
                }
            ],
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert len(tables.jobs_table.scan()['Items']) == 1


@pytest.mark.network
def test_opera_rtc_s1_hh(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {'granules': ['S1_011394_IW2_20200102T024334_HH_86EB-BURST']},
                }
            ],
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert len(tables.jobs_table.scan()['Items']) == 1


@pytest.mark.network
def test_opera_rtc_s1_validation_order(client, tables, approved_user, monkeypatch):
    """Test that the validators are applied in the expected order."""
    login(client, username=approved_user)

    payload = {
        'jobs': [
            {
                'job_type': 'OPERA_RTC_S1',
                'job_parameters': {'granules': ['S1_271383_IW1_20160101T095550_HH_51B7-BURST']},
            }
        ]
    }

    response = client.post(JOBS_URI, json=payload)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'acquired before 2016-04-14' in response.json['detail']
    assert len(tables.jobs_table.scan()['Items']) == 0

    monkeypatch.setattr(hyp3_api.validation, 'check_opera_rtc_s1_date', MagicMock())
    response = client.post(JOBS_URI, json=payload)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'DEM coverage' in response.json['detail']
    assert len(tables.jobs_table.scan()['Items']) == 0

    monkeypatch.setattr(hyp3_api.validation, 'check_dem_coverage', MagicMock())
    response = client.post(JOBS_URI, json=payload)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'outside of the OPERA RTC S1 processing extent' in response.json['detail']
    assert len(tables.jobs_table.scan()['Items']) == 0

    monkeypatch.setattr(hyp3_api.validation, 'check_opera_rtc_s1_static_coverage', MagicMock())
    response = client.post(JOBS_URI, json=payload)

    assert response.status_code == HTTPStatus.OK
    assert len(tables.jobs_table.scan()['Items']) == 1


@pytest.mark.network
def test_opera_rtc_s1_min_date(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {'granules': ['S1_177314_IW3_20160110T095124_VV_AE7B-BURST']},
                }
            ],
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert (
        response.json['detail'] == 'Granule S1_177314_IW3_20160110T095124_VV_AE7B-BURST was acquired before 2016-04-14 '
        'and is not available for On Demand OPERA RTC S1 processing.'
    )
    assert len(tables.jobs_table.scan()['Items']) == 0


@pytest.mark.network
def test_opera_rtc_s1_max_date(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {'granules': ['S1_189138_IW2_20230801T185545_VV_68B0-BURST']},
                }
            ],
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert (
        response.json['detail']
        == 'Granule S1_189138_IW2_20230801T185545_VV_68B0-BURST was acquired on or after 2022-01-01 '
        'and is not available for On Demand OPERA RTC S1 processing. '
        'You can download the product from the ASF DAAC archive.'
    )
    assert len(tables.jobs_table.scan()['Items']) == 0


@pytest.mark.network
def test_opera_rtc_s1_static_coverage(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {'granules': ['S1_363644_IW2_20200101T083656_HH_267E-BURST']},
                }
            ],
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert (
        response.json['detail']
        == 'Granule S1_363644_IW2_20200101T083656_HH_267E-BURST is outside of the OPERA RTC S1 processing extent.'
    )
    assert len(tables.jobs_table.scan()['Items']) == 0


@pytest.mark.network
def test_opera_rtc_s1_dem_coverage(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {'granules': ['S1_157213_IW3_20190210T182738_HH_D6C8-BURST']},
                }
            ],
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert (
        response.json['detail']
        == 'Some requested scenes do not have DEM coverage: S1_157213_IW3_20190210T182738_HH_D6C8-BURST'
    )
    assert len(tables.jobs_table.scan()['Items']) == 0


@pytest.mark.network
def test_opera_rtc_s1_nonexistent_granule(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {'granules': ['S1_157213_IW3_20190210T182738_HH_D6C7-BURST']},
                }
            ],
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert (
        response.json['detail']
        == 'Some requested scenes could not be found: S1_157213_IW3_20190210T182738_HH_D6C7-BURST'
    )
    assert len(tables.jobs_table.scan()['Items']) == 0
