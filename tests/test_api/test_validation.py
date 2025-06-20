import contextlib
import inspect
from unittest import mock

import pytest
import responses
from shapely.geometry import Polygon

from hyp3_api import CMR_URL, multi_burst_validation, validation
from test_api.conftest import FUTURE_DATE, setup_mock_cmr_response_for_polygons


def rectangle(north, south, east, west):
    return Polygon([[west, north], [east, north], [east, south], [west, south]])


def test_not_antimeridian():
    # Wyoming
    good_rect = rectangle(45, 41, -104, -111)

    # Aleutian Islands over antimeridian; should fail
    bad_rect = rectangle(51.7, 51.3, 179.7, -179.3)

    good_granules = [{'polygon': good_rect, 'name': 'good'}, {'polygon': good_rect, 'name': 'good'}]
    validation.check_not_antimeridian({}, good_granules)

    bad_granules = [{'polygon': good_rect, 'name': 'good'}, {'polygon': bad_rect, 'name': 'bad'}]
    with pytest.raises(validation.ValidationError, match=r'.*crosses the antimeridian.*'):
        validation.check_not_antimeridian({}, bad_granules)


def test_has_sufficient_coverage():
    # Wyoming
    poly = rectangle(45, 41, -104, -111)
    assert validation._has_sufficient_coverage(poly)

    # completely covered Aleutian Islands over antimeridian; should pass with fixed antimeridian
    poly = rectangle(51.7, 51.3, 179.7, -179.3)
    assert validation._has_sufficient_coverage(poly)

    # not enough coverage of Aleutian Islands over antimeridian
    # NOTE: Passes today but should FAIL legacy with antimeridian feature fix
    poly = rectangle(51.7, 41.3, 179.7, -179.3)
    assert validation._has_sufficient_coverage(poly)

    # completely encloses tile over Ascension Island in the Atlantic
    poly = rectangle(-6, -9, -15, -14)
    assert validation._has_sufficient_coverage(poly)

    # # minimum sufficient coverage off the coast of Eureka, CA
    poly = rectangle(40.1, 40, -126, -125.000138)
    assert validation._has_sufficient_coverage(poly)

    # almost minimum sufficient coverage off the coast of Eureka, CA
    poly = rectangle(40.1, 40, -126, -125.000140)
    assert not validation._has_sufficient_coverage(poly)

    # polygon in missing tile over Gulf of California
    poly = rectangle(26.9, 26.1, -110.1, -110.9)
    assert not validation._has_sufficient_coverage(poly)

    # southern Greenland
    poly = rectangle(62, 61, -44, -45)
    assert validation._has_sufficient_coverage(poly)

    # Antarctica
    poly = rectangle(-62, -90, 180, -180)
    assert validation._has_sufficient_coverage(poly)

    # ocean over antimeridian; this case incorrectly passes, see https://github.com/ASFHyP3/hyp3/issues/1989
    poly = rectangle(-40, -41, 179.7, -179.3)
    assert validation._has_sufficient_coverage(poly)


def test_format_points():
    point_string = '-31.43 25.04 -29.76 25.54 -29.56 24.66 -31.23 24.15 -31.43 25.04'
    assert validation._format_points(point_string) == [
        [25.04, -31.43],
        [25.54, -29.76],
        [24.66, -29.56],
        [24.15, -31.23],
        [25.04, -31.43],
    ]


def test_check_dem_coverage():
    covered1 = {'name': 'covered1', 'polygon': rectangle(45, 41, -104, -111)}
    covered2 = {'name': 'covered2', 'polygon': rectangle(-62, -90, 180, -180)}
    not_covered = {'name': 'not_covered', 'polygon': rectangle(-20, -30, 70, 100)}

    validation.check_dem_coverage({}, [])
    validation.check_dem_coverage({}, [covered1])
    validation.check_dem_coverage({}, [covered2])
    validation.check_dem_coverage({}, [covered1, covered2])

    with pytest.raises(validation.ValidationError) as e:
        validation.check_dem_coverage({}, [not_covered])
    assert 'not_covered' in str(e)

    with pytest.raises(validation.ValidationError) as e:
        validation.check_dem_coverage({}, [covered1, not_covered])
    assert 'not_covered' in str(e)
    assert 'covered1' not in str(e)


def test_check_multi_burst_pairs():
    with mock.patch.object(multi_burst_validation, 'validate_bursts') as mock_validate_bursts:
        validation.check_multi_burst_pairs(
            {'job_parameters': {'reference': 'mock_reference', 'secondary': 'mock_secondary'}}, None
        )

        mock_validate_bursts.assert_called_once_with('mock_reference', 'mock_secondary')


def test_check_multi_burst_max_length():
    job_with_15_pairs = {'job_parameters': {'reference': list(range(15)), 'secondary': list(range(15))}}
    job_with_16_reference = {'job_parameters': {'reference': list(range(16)), 'secondary': list(range(15))}}
    job_with_16_secondary = {'job_parameters': {'reference': list(range(15)), 'secondary': list(range(16))}}

    validation.check_multi_burst_max_length(job_with_15_pairs, None)

    with pytest.raises(
        multi_burst_validation.MultiBurstValidationError,
        match=r'^Must provide no more than 15 scene pairs, got 16 reference and 15 secondary$',
    ):
        validation.check_multi_burst_max_length(job_with_16_reference, None)

    with pytest.raises(
        multi_burst_validation.MultiBurstValidationError,
        match=r'^Must provide no more than 15 scene pairs, got 15 reference and 16 secondary$',
    ):
        validation.check_multi_burst_max_length(job_with_16_secondary, None)

    with pytest.raises(
        multi_burst_validation.MultiBurstValidationError,
        match=r'^Must provide no more than 14 scene pairs, got 15 reference and 15 secondary$',
    ):
        validation.check_multi_burst_max_length(job_with_15_pairs, None, max_pairs=14)


def test_check_single_burst_pair():
    valid_job = {
        'job_parameters': {
            'granules': [
                'S1_136231_IW2_20200604T022312_VV_7C85-BURST',
                'S1_136231_IW2_20200616T022313_VV_5D11-BURST',
            ]
        }
    }
    validation.check_single_burst_pair(valid_job, None)

    invalid_job_different_number = {
        'job_parameters': {
            'granules': [
                'S1_136231_IW2_20200604T022312_VV_7C85-BURST',
                'S1_136232_IW2_20200616T022313_VV_5D11-BURST',
            ]
        }
    }
    with pytest.raises(
        validation.ValidationError,
        match=r'^Burst IDs do not match for S1_136231_IW2_20200604T022312_VV_7C85-BURST and '
        r'S1_136232_IW2_20200616T022313_VV_5D11-BURST\.$',
    ):
        validation.check_single_burst_pair(invalid_job_different_number, None)

    invalid_job_different_swath = {
        'job_parameters': {
            'granules': [
                'S1_136231_IW2_20200604T022312_VV_7C85-BURST',
                'S1_136231_IW3_20200616T022313_VV_5D11-BURST',
            ]
        }
    }
    with pytest.raises(
        validation.ValidationError,
        match=r'^Burst IDs do not match for S1_136231_IW2_20200604T022312_VV_7C85-BURST and '
        r'S1_136231_IW3_20200616T022313_VV_5D11-BURST\.$',
    ):
        validation.check_single_burst_pair(invalid_job_different_swath, None)

    invalid_job_different_pol = {
        'job_parameters': {
            'granules': [
                'S1_136231_IW2_20200604T022312_VV_7C85-BURST',
                'S1_136231_IW2_20200616T022313_HH_5D11-BURST',
            ]
        }
    }
    with pytest.raises(
        validation.ValidationError,
        match=r'^The requested scenes need to have the same polarization, got: VV, HH$',
    ):
        validation.check_single_burst_pair(invalid_job_different_pol, None)

    invalid_job_unsupported_pol = {
        'job_parameters': {
            'granules': [
                'S1_136231_IW2_20200604T022312_VH_7C85-BURST',
                'S1_136231_IW2_20200616T022313_VH_5D11-BURST',
            ]
        }
    }
    with pytest.raises(
        validation.ValidationError, match=r'^Only VV and HH polarizations are currently supported, got: VH$'
    ):
        validation.check_single_burst_pair(invalid_job_unsupported_pol, None)


def test_make_sure_granules_exist():
    granule_metadata = [
        {
            'name': 'scene1',
        },
        {
            'name': 'scene2',
        },
    ]

    validation._make_sure_granules_exist([], granule_metadata)
    validation._make_sure_granules_exist(['scene1'], granule_metadata)
    validation._make_sure_granules_exist(['scene1', 'scene2'], granule_metadata)

    with pytest.raises(validation.ValidationError) as e:
        validation._make_sure_granules_exist(
            ['scene1', 'scene2', 'scene3', 'scene4', 'S2_foo', 'LC08_bar', 'LC09_bar'], granule_metadata
        )
    assert 'S2_foo' not in str(e)
    assert 'LC08_bar' not in str(e)
    assert 'LC09_bar' not in str(e)
    assert 'scene1' not in str(e)
    assert 'scene2' not in str(e)
    assert 'scene3' in str(e)
    assert 'scene4' in str(e)


def test_is_third_party_granule():
    assert validation._is_third_party_granule('S2A_MSIL1C_20200627T150921_N0209_R025_T22WEB_20200627T170912')
    assert validation._is_third_party_granule('S2B_22WEB_20200612_0_L1C')
    assert validation._is_third_party_granule('LC08_L1TP_009011_20200820_20200905_02_T1')
    assert validation._is_third_party_granule('LO08_L1GT_043001_20201106_20201110_02_T2')
    assert validation._is_third_party_granule('LT08_L1GT_041001_20200125_20200925_02_T2')
    assert validation._is_third_party_granule('LC09_L1GT_215109_20220125_20220125_02_T2')
    assert validation._is_third_party_granule('LO09_L1GT_215109_20220210_20220210_02_T2')
    assert validation._is_third_party_granule('LT09_L1GT_215109_20220210_20220210_02_T2')
    assert not validation._is_third_party_granule('S1_249434_IW1_20230523T170733_VV_8850-BURST')
    assert not validation._is_third_party_granule('S1A_IW_SLC__1SSH_20150608T205059_20150608T205126_006287_0083E8_C4F0')
    assert not validation._is_third_party_granule('foo')


@responses.activate
def test_get_cmr_metadata():
    response_payload = {
        'feed': {
            'entry': [
                {
                    'producer_granule_id': 'foo',
                    'polygons': [['-31.4 25.0 -29.7 25.5 -29.5 24.6 -31.2 24.1 -31.4 25.0']],
                },
                {
                    'title': 'bar',
                    'polygons': [['0 1 2 3 4 5 6 7 0 1']],
                },
            ],
        },
    }
    responses.post(CMR_URL, json=response_payload)

    assert validation._get_cmr_metadata(['foo', 'bar', 'hello']) == [
        {
            'name': 'foo',
            'polygon': Polygon([[25.0, -31.4], [25.5, -29.7], [24.6, -29.5], [24.1, -31.2]]),
        },
        {
            'name': 'bar',
            'polygon': Polygon([[1, 0], [3, 2], [5, 4], [7, 6]]),
        },
    ]


@responses.activate
def test_validate_jobs():
    unknown_granule = 'unknown'
    granule_with_dem_coverage = 'S1A_IW_SLC__1SSV_20150621T120220_20150621T120232_006471_008934_72D8'
    granule_without_dem_coverage = 'S1A_IW_GRDH_1SDV_20201219T222530_20201219T222555_035761_042F72_8378'

    granule_polygon_pairs = [
        (
            granule_with_dem_coverage,
            [
                [
                    '13.705972 -91.927132 14.452647 -91.773392 14.888498 -94.065727 '
                    '14.143632 -94.211563 13.705972 -91.927132'
                ]
            ],
        ),
        (
            granule_without_dem_coverage,
            [
                [
                    '37.796551 -68.331245 36.293144 -67.966415 36.69714 -65.129745 '
                    '38.198883 -65.437325 37.796551 -68.331245'
                ]
            ],
        ),
    ]
    setup_mock_cmr_response_for_polygons(granule_polygon_pairs)

    jobs = [
        {
            'job_type': 'RTC_GAMMA',
            'job_parameters': {
                'granules': [granule_with_dem_coverage],
            },
        },
        {
            'job_type': 'RTC_GAMMA',
            'job_parameters': {
                'granules': [granule_with_dem_coverage],
                'dem_name': 'copernicus',
            },
        },
        {
            'job_type': 'INSAR_GAMMA',
            'job_parameters': {
                'granules': [granule_with_dem_coverage, granule_with_dem_coverage],
            },
        },
        {
            'job_type': 'AUTORIFT',
            'job_parameters': {
                'granules': [granule_with_dem_coverage, granule_without_dem_coverage],
            },
        },
        {'job_type': 'ARIA_RAIDER', 'job_parameters': {}},
    ]
    validation.validate_jobs(jobs)

    jobs = [
        {
            'job_type': 'RTC_GAMMA',
            'job_parameters': {
                'granules': [unknown_granule],
            },
        }
    ]
    with pytest.raises(validation.ValidationError):
        validation.validate_jobs(jobs)

    jobs = [
        {
            'job_type': 'RTC_GAMMA',
            'job_parameters': {
                'granules': [granule_without_dem_coverage],
            },
        }
    ]
    with pytest.raises(validation.ValidationError):
        validation.validate_jobs(jobs)


def test_all_validators_have_correct_signature():
    validators = [getattr(validation, attr) for attr in dir(validation) if attr.startswith('check_')]

    for validator in validators:
        function_params = list(inspect.signature(validator).parameters)

        assert len(function_params) >= 2
        assert function_params[0] in ('job', '_')
        assert function_params[1] in ('granule_metadata', '_')


def test_check_bounds_formatting():
    valid_jobs = [
        {'job_parameters': {'bounds': [-10, 0, 10, 10]}},
        {'job_parameters': {'bounds': [-180, -90, -170, -80]}},
        {'job_parameters': {'bounds': [170, 75, 180, 90]}},
    ]
    invalid_jobs_bad_order = [
        {'job_parameters': {'bounds': [10, 0, -10, 10]}},
        {'job_parameters': {'bounds': [-10, 10, 10, 0]}},
        {'job_parameters': {'bounds': [10, 0, 10, 10]}},
        {'job_parameters': {'bounds': [-10, 0, 10, 0]}},
    ]
    invalid_jobs_bad_values = [
        {'job_parameters': {'bounds': [-10, 0, 10, 100]}},
        {'job_parameters': {'bounds': [-200, 0, 10, 10]}},
        {'job_parameters': {'bounds': [-10, -100, 10, 80]}},
        {'job_parameters': {'bounds': [-100, 0, 200, 10]}},
    ]

    job_with_bad_bounds = {'job_parameters': {'bounds': [0, 0, 0, 0]}}

    for valid_job in valid_jobs:
        validation.check_bounds_formatting(valid_job, {})
    for invalid_job in invalid_jobs_bad_order:
        with pytest.raises(validation.ValidationError, match=r'.*Invalid order for bounds.*'):
            validation.check_bounds_formatting(invalid_job, {})
    for invalid_job in invalid_jobs_bad_values:
        with pytest.raises(validation.ValidationError, match=r'.*Invalid lon/lat value(s)*'):
            validation.check_bounds_formatting(invalid_job, {})

    with pytest.raises(validation.ValidationError, match=r'.*Bounds cannot be.*'):
        validation.check_bounds_formatting(job_with_bad_bounds, {})


def test_check_granules_intersecting_bounds():
    job_with_specified_bounds = {'job_parameters': {'bounds': [-10, 0, 10, 10]}}
    job_with_bad_bounds = {'job_parameters': {'bounds': [0, 0, 0, 0]}}
    valid_granule_metadata = [
        {'name': 'intersects1', 'polygon': Polygon.from_bounds(-10.0, 0.0, 10.0, 10.0)},
        {'name': 'intersects2', 'polygon': Polygon.from_bounds(-9.0, -1.0, 20.0, 11.0)},
        {'name': 'intersects3', 'polygon': Polygon.from_bounds(0.0, 5.0, 15.0, 15.0)},
    ]
    invalid_granule_metadata = [
        {'name': 'intersects1', 'polygon': Polygon.from_bounds(-10.0, 0.0, 10.0, 10.0)},
        {'name': 'does_not_intersect1', 'polygon': Polygon.from_bounds(10.1, -10, 20.0, -0.1)},
        {'name': 'intersects2', 'polygon': Polygon.from_bounds(-9.0, -1.0, 20.0, 11.0)},
        {'name': 'does_not_intersect2', 'polygon': Polygon.from_bounds(-80.0, 20.0, -60.0, 90.0)},
        {'name': 'does_not_intersect3', 'polygon': Polygon.from_bounds(100.0, -50.0, 120.0, -0.1)},
    ]
    validation.check_granules_intersecting_bounds(job_with_specified_bounds, valid_granule_metadata)

    error_pattern = r'.*Bounds cannot be.*'
    with pytest.raises(validation.ValidationError, match=error_pattern):
        validation.check_granules_intersecting_bounds(job_with_bad_bounds, valid_granule_metadata)

    with pytest.raises(validation.ValidationError, match=error_pattern):
        validation.check_granules_intersecting_bounds(job_with_bad_bounds, invalid_granule_metadata)

    error_pattern = r".*bounds: \['does_not_intersect1', 'does_not_intersect2', 'does_not_intersect3'\]*"

    with pytest.raises(validation.ValidationError, match=error_pattern):
        validation.check_granules_intersecting_bounds(job_with_specified_bounds, invalid_granule_metadata)


def test_check_same_relative_orbits():
    valid_granule_metadata = [
        {'name': 'S1A_IW_RAW__0SDV_20201015T161622_20201015T161654_034809_040E95_AF3C'},
        {'name': 'S1A_IW_RAW__0SDV_20200816T161620_20200816T161652_033934_03EFCE_5730'},
        {'name': 'S1B_IW_RAW__0SDV_20200810T161537_20200810T161610_022863_02B66A_F7D7'},
        {'name': 'S1B_IW_RAW__0SDV_20200623T161535_20200623T161607_022163_02A10F_7FD6'},
    ]
    invalid_granule_metadata = valid_granule_metadata.copy()
    invalid_granule_metadata.append({'name': 'S1B_IW_RAW__0SDV_20200623T161535_20200623T161607_012345_02A10F_7FD6'})
    validation.check_same_relative_orbits({}, valid_granule_metadata)
    error_pattern = r'.*69 is not 87.*'
    with pytest.raises(validation.ValidationError, match=error_pattern):
        validation.check_same_relative_orbits({}, invalid_granule_metadata)


def test_check_bounding_box_size():
    job = {'job_parameters': {'bounds': [0, 0, 10, 10]}}

    validation.check_bounding_box_size(job, None, max_bounds_area=100)

    error_pattern = r'.*Bounds must be smaller.*'
    with pytest.raises(validation.ValidationError, match=error_pattern):
        validation.check_bounding_box_size(job, None, max_bounds_area=99.9)


def test_check_opera_rtc_s1_bounds():
    granule_metadata = [
        {
            'name': 'valid1',
            'polygon': rectangle(-59.99, -60.01, -180, -179),
        },
        {
            'name': 'valid2',
            'polygon': rectangle(0, 1, 0, 1),
        },
    ]
    validation.check_opera_rtc_s1_bounds(None, granule_metadata)

    granule_metadata.append(
        {
            'name': 'invalid',
            'polygon': rectangle(-60.01, -61, 23, 24),
        }
    )
    with pytest.raises(validation.ValidationError, match=r'Granule invalid is south of -60 degrees latitude'):
        validation.check_opera_rtc_s1_bounds(None, granule_metadata)


def test_check_opera_rtc_s1_date_1_granule():
    with pytest.raises(validation.InternalValidationError, match=r'^Expected 1 granule.*'):
        validation.check_opera_rtc_s1_date(
            {'job_parameters': {'granules': ['foo', 'bar']}},
            None,
        )

    with pytest.raises(validation.InternalValidationError, match=r'^Expected 1 granule.*'):
        validation.check_opera_rtc_s1_date(
            {'job_parameters': {'granules': []}},
            None,
        )


def test_check_opera_rtc_s1_date_min():
    validation.check_opera_rtc_s1_date(
        {'job_parameters': {'granules': ['S1_000000_IW1_20160414T000000_VV_0000-BURST']}}, None
    )

    with pytest.raises(
        validation.ValidationError,
        match=r'^Granule S1_000000_IW1_20160413T235959_VV_0000-BURST was acquired before 2016-04-14 .*$',
    ):
        validation.check_opera_rtc_s1_date(
            {'job_parameters': {'granules': ['S1_000000_IW1_20160413T235959_VV_0000-BURST']}}, None
        )


def test_check_opera_rtc_s1_date_max():
    validation.check_opera_rtc_s1_date(
        {'job_parameters': {'granules': ['S1_000000_IW1_20211231T235959_VV_0000-BURST']}}, None
    )

    with pytest.raises(
        validation.ValidationError,
        match=r'^Granule S1_000000_IW1_20220101T000000_VV_0000-BURST was acquired on or after 2022-01-01 .*',
    ):
        validation.check_opera_rtc_s1_date(
            {'job_parameters': {'granules': ['S1_000000_IW1_20220101T000000_VV_0000-BURST']}}, None
        )

    with pytest.raises(
        validation.ValidationError,
        match=r'^Granule S1_000000_IW1_20250428T000000_VV_0000-BURST was acquired on or after 2022-01-01 .*',
    ):
        validation.check_opera_rtc_s1_date(
            {'job_parameters': {'granules': ['S1_000000_IW1_20250428T000000_VV_0000-BURST']}}, None
        )


def test_check_opera_rtc_s1_date_max_configurable(monkeypatch):
    monkeypatch.setenv('OPERA_RTC_S1_END_DATE', '2025-05-02')

    validation.check_opera_rtc_s1_date(
        {'job_parameters': {'granules': ['S1_000000_IW1_20250501T235959_VV_0000-BURST']}}, None
    )

    with pytest.raises(
        validation.ValidationError,
        match=r'^Granule S1_000000_IW1_20250502T000000_VV_0000-BURST was acquired on or after 2025-05-02 .*',
    ):
        validation.check_opera_rtc_s1_date(
            {'job_parameters': {'granules': ['S1_000000_IW1_20250502T000000_VV_0000-BURST']}}, None
        )

    with pytest.raises(
        validation.ValidationError,
        match=r'^Granule S1_000000_IW1_20250506T000000_VV_0000-BURST was acquired on or after 2025-05-02 .*',
    ):
        validation.check_opera_rtc_s1_date(
            {'job_parameters': {'granules': ['S1_000000_IW1_20250506T000000_VV_0000-BURST']}}, None
        )


@pytest.mark.parametrize(
    'job_parameters,error',
    [
        ({'reference_date': '2022-01-02', 'secondary_date': '2022-01-01'}, contextlib.nullcontext()),
        (
            {'reference_date': '2014-06-14', 'secondary_date': '2022-01-02'},
            pytest.raises(validation.ValidationError, match=r'.*is before the start of the sentinel 1 mission.*'),
        ),
        (
            {'reference_date': '2022-01-02', 'secondary_date': '2014-06-14'},
            pytest.raises(validation.ValidationError, match=r'.*is before the start of the sentinel 1 mission.*'),
        ),
        (
            {'reference_date': FUTURE_DATE, 'secondary_date': '2021-01-01'},
            pytest.raises(validation.ValidationError, match=r'.*is a date in the future.*'),
        ),
        (
            {'reference_date': '2021-01-01', 'secondary_date': FUTURE_DATE},
            pytest.raises(validation.ValidationError, match=r'.*is a date in the future.*'),
        ),
        (
            {'reference_date': '2021-01-01', 'secondary_date': '2021-01-01'},
            pytest.raises(validation.ValidationError, match=r'secondary date must be earlier than reference date\.'),
        ),
        (
            {'reference_date': '2022-01-01', 'secondary_date': '2022-01-02'},
            pytest.raises(validation.ValidationError, match=r'secondary date must be earlier than reference date\.'),
        ),
    ],
)
def test_check_aria_s1_gunw_dates(job_parameters, error):
    with error:
        validation.check_aria_s1_gunw_dates({'job_parameters': job_parameters}, None)
