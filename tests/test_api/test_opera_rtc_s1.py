from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
import responses

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
    assert 'outside the valid processing extent for OPERA RTC-S1 products' in response.json['detail']
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
def test_opera_rtc_s1_static_coverage(client, tables, approved_user):
    login(client, username=approved_user)

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {'granules': ['S1_175498_IW2_20160415T082755_HH_C4A7-BURST']},
                }
            ],
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert (
        response.json['detail'] == 'Granule S1_175498_IW2_20160415T082755_HH_C4A7-BURST is outside the valid '
        'processing extent for OPERA RTC-S1 products.'
    )
    assert len(tables.jobs_table.scan()['Items']) == 0


@responses.activate
def test_opera_rtc_s1_static_coverage_cmr_error(client, tables, approved_user, monkeypatch):
    login(client, username=approved_user)

    mock_get_cmr_metadata = MagicMock()
    monkeypatch.setattr(hyp3_api.validation, '_get_cmr_metadata', mock_get_cmr_metadata)

    mock_make_sure_granules_exist = MagicMock()
    monkeypatch.setattr(hyp3_api.validation, '_make_sure_granules_exist', mock_make_sure_granules_exist)

    mock_check_dem_coverage = MagicMock()
    monkeypatch.setattr(hyp3_api.validation, 'check_dem_coverage', mock_check_dem_coverage)

    params = {
        'short_name': 'OPERA_L2_RTC-S1-STATIC_V1',
        'granule_ur': 'OPERA_L2_RTC-S1-STATIC_T*-175498-IW2_*',
        'options[granule_ur][pattern]': 'true',
    }
    responses.get(
        url=hyp3_api.CMR_URL,
        match=[responses.matchers.query_param_matcher(params)],
        status=500,
    )

    response = client.post(
        JOBS_URI,
        json={
            'jobs': [
                {
                    'job_type': 'OPERA_RTC_S1',
                    'job_parameters': {'granules': ['S1_175498_IW2_20160415T082755_HH_C4A7-BURST']},
                }
            ],
        },
    )

    mock_get_cmr_metadata.assert_called_once()
    mock_make_sure_granules_exist.assert_called_once()
    mock_check_dem_coverage.assert_called_once()

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json['detail'] == 'Could not submit jobs due to a CMR error. Please try again later.'
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
