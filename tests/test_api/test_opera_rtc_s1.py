from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
import responses

import hyp3_api.validation
from test_api.conftest import CMR_URL_RE, JOBS_URI, login


@pytest.mark.network
def test_opera_rtc_s1_vv(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {'granules': ['S1_073251_IW2_20200128T020712_VV_2944-BURST']},
                }
            ],
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert len(tables.jobs_table.scan()['Items']) == 1


def test_opera_rtc_s1_vh(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {'granules': ['S1_073251_IW2_20200128T020712_VH_2944-BURST']},
                }
            ],
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'is not valid under any of the given schemas' in response.json['detail']
    assert len(tables.jobs_table.scan()['Items']) == 0


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


def test_opera_rtc_s1_hv(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {'granules': ['S1_011394_IW2_20200102T024334_HV_86EB-BURST']},
                }
            ],
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'is not valid under any of the given schemas' in response.json['detail']
    assert len(tables.jobs_table.scan()['Items']) == 0


def test_opera_rtc_s1_ew(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {'granules': ['S1_148167_EW5_20201225T230343_VV_BB1F-BURST']},
                }
            ],
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'is not valid under any of the given schemas' in response.json['detail']
    assert len(tables.jobs_table.scan()['Items']) == 0


def test_opera_rtc_s1_multi_burst(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {
                        'granules': [
                            'S1_073251_IW2_20200128T020712_VV_2944-BURST',
                            'S1_073251_IW2_20200128T020712_VV_2944-BURST',
                        ]
                    },
                }
            ],
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'is not valid under any of the given schemas' in response.json['detail']
    assert len(tables.jobs_table.scan()['Items']) == 0


@pytest.mark.network
def test_opera_rtc_s1_validation_order(client, tables, approved_user, monkeypatch):
    """Test that the validators are applied in the expected order."""
    login(client, username=approved_user)

    payload = {
        'jobs': [
            {
                'job_type': 'OPERA_RTC_S1',
                'job_parameters': {'granules': ['S1_190713_IW1_20151030T200722_HH_617F-BURST']},
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
    assert 'outside the valid processing extent for OPERA RTC-S1 products' in response.json['detail']
    assert len(tables.jobs_table.scan()['Items']) == 0

    monkeypatch.setattr(hyp3_api.validation, 'check_opera_rtc_s1_bounds', MagicMock())
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
        'and is not available for On-Demand OPERA RTC-S1 processing.'
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
        'and is not available for On-Demand OPERA RTC-S1 processing. '
        'You can download the product from the ASF DAAC archive.'
    )
    assert len(tables.jobs_table.scan()['Items']) == 0


@pytest.mark.network
def test_opera_rtc_s1_max_date_configurable(client, tables, approved_user, monkeypatch):
    login(client, username=approved_user)

    monkeypatch.setenv('OPERA_RTC_S1_END_DATE', '2020-01-01')

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {'granules': ['S1_073251_IW2_20200128T020712_VV_2944-BURST']},
                }
            ],
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert (
        response.json['detail']
        == 'Granule S1_073251_IW2_20200128T020712_VV_2944-BURST was acquired on or after 2020-01-01 '
        'and is not available for On-Demand OPERA RTC-S1 processing. '
        'You can download the product from the ASF DAAC archive.'
    )
    assert len(tables.jobs_table.scan()['Items']) == 0


@pytest.mark.network
def test_opera_rtc_s1_bounds(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {'granules': ['S1_018641_IW1_20180307T081710_HH_20C9-BURST']},
                }
            ],
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert (
        response.json['detail'] == 'Granule S1_018641_IW1_20180307T081710_HH_20C9-BURST is south of -60 degrees '
        'latitude and outside the valid processing extent for OPERA RTC-S1 products.'
    )
    assert len(tables.jobs_table.scan()['Items']) == 0


@responses.activate
def test_opera_rtc_s1_bounds_cmr_error(client, tables, approved_user):
    login(client, username=approved_user)

    responses.post(url=CMR_URL_RE, status=500)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {'granules': ['S1_018641_IW1_20180307T081710_HH_20C9-BURST']},
                }
            ],
        },
    )

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json['detail'] == 'Cannot validate job(s) of type OPERA_RTC_S1 because CMR query failed. Please try again later.'
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
