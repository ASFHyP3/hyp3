import responses
from pytest import raises
from shapely.geometry import Polygon
from test_api.conftest import setup_requests_mock_with_given_polygons

from hyp3_api import CMR_URL, validation


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
    with raises(validation.GranuleValidationError, match=r'.*crosses the antimeridian.*'):
        validation.check_not_antimeridian({}, bad_granules)


def test_has_sufficient_coverage():
    # Wyoming
    poly = rectangle(45, 41, -104, -111)
    assert validation.has_sufficient_coverage(poly)

    # completely covered Aleutian Islands over antimeridian; should pass with fixed antimeridian
    poly = rectangle(51.7, 51.3, 179.7, -179.3)
    assert validation.has_sufficient_coverage(poly)

    # not enough coverage of Aleutian Islands over antimeridian
    # NOTE: Passes today but should FAIL legacy with antimeridian feature fix
    poly = rectangle(51.7, 41.3, 179.7, -179.3)
    assert validation.has_sufficient_coverage(poly)

    # completely encloses tile over Ascension Island in the Atlantic
    poly = rectangle(-6, -9, -15, -14)
    assert validation.has_sufficient_coverage(poly)

    # # minimum sufficient coverage off the coast of Eureka, CA
    poly = rectangle(40.1, 40, -126, -125.000138)
    assert validation.has_sufficient_coverage(poly)

    # almost minimum sufficient coverage off the coast of Eureka, CA
    poly = rectangle(40.1, 40, -126, -125.000140)
    assert not validation.has_sufficient_coverage(poly)

    # polygon in missing tile over Gulf of California
    poly = rectangle(26.9, 26.1, -110.1, -110.9)
    assert not validation.has_sufficient_coverage(poly)

    # southern Greenland
    poly = rectangle(62, 61, -44, -45)
    assert validation.has_sufficient_coverage(poly)

    # Antarctica
    poly = rectangle(-62, -90, 180, -180)
    assert validation.has_sufficient_coverage(poly)

    # ocean over antimeridian; this case incorrectly passes, see https://github.com/ASFHyP3/hyp3/issues/1989
    poly = rectangle(-40, -41, 179.7, -179.3)
    assert validation.has_sufficient_coverage(poly)


def test_format_points():
    point_string = '-31.43 25.04 -29.76 25.54 -29.56 24.66 -31.23 24.15 -31.43 25.04'
    assert validation.format_points(point_string) == [
        [25.04, -31.43],
        [25.54, -29.76],
        [24.66, -29.56],
        [24.15, -31.23],
        [25.04, -31.43]
    ]


def test_check_dem_coverage():
    covered1 = {'name': 'covered1', 'polygon': rectangle(45, 41, -104, -111)}
    covered2 = {'name': 'covered2', 'polygon': rectangle(-62, -90, 180, -180)}
    not_covered = {'name': 'not_covered', 'polygon': rectangle(-20, -30, 70, 100)}

    validation.check_dem_coverage({}, [])
    validation.check_dem_coverage({}, [covered1])
    validation.check_dem_coverage({}, [covered2])
    validation.check_dem_coverage({}, [covered1, covered2])

    with raises(validation.GranuleValidationError) as e:
        validation.check_dem_coverage({}, [not_covered])
    assert 'not_covered' in str(e)

    with raises(validation.GranuleValidationError) as e:
        validation.check_dem_coverage({}, [covered1, not_covered])
    assert 'not_covered' in str(e)
    assert 'covered1' not in str(e)


def test_check_same_burst_ids():
    valid_jobs = [
        {
            'job_parameters': {
                'reference': ['S1_136231_IW2_20200604T022312_VV_7C85-BURST'],
                'secondary': ['S1_136231_IW2_20200616T022313_VV_5D11-BURST']
            }
        },
        {
            'job_parameters': {
                'reference': [
                    'S1_136231_IW2_20200604T022312_VV_7C85-BURST',
                    'S1_136232_IW2_20200616T022315_VV_5D11-BURST'
                ],
                'secondary': [
                    'S1_136231_IW2_20200616T022313_VV_5411-BURST',
                    'S1_136232_IW2_20200616T022345_VV_5D13-BURST'
                ]
            }
        },
        {
            'job_parameters': {
                'reference': [
                    'S1_136231_IW2_20200604T022312_VV_7C85-BURST',
                    'S1_136231_IW3_20200616T022315_VV_5D11-BURST'
                ],
                'secondary': [
                    'S1_136231_IW2_20200616T022313_VV_5411-BURST',
                    'S1_136231_IW3_20200616T022345_VV_5D13-BURST'
                ]
            }
        }
    ]
    invalid_job_different_lengths = {
        'job_parameters': {
            'reference': ['S1_136231_IW2_20200604T022312_VV_7C85-BURST'],
            'secondary': [
                'S1_136232_IW2_20200616T022313_VV_5D11-BURST',
                'S1_136233_IW2_20200616T022313_VV_5D11-BURST'
            ]
        }
    }
    invalid_jobs_not_matching = [
        {
            'job_parameters': {
                'reference': ['S1_136231_IW2_20200604T022312_VV_7C85-BURST'],
                'secondary': ['S1_136232_IW2_20200616T022313_VV_5D11-BURST']
            }
        },
        {
            'job_parameters': {
                'reference': [
                    'S1_136231_IW2_20200604T022312_VV_7C85-BURST',
                    'S1_136232_IW2_20200604T123455_VV_ABC5-BURST'
                ],
                'secondary': [
                    'S1_136231_IW2_20200617T022313_VV_5D11-BURST',
                    'S1_136233_IW2_20200617T123213_VV_5E13-BURST'
                ]
            }
        },
        {
            'job_parameters': {
                'reference': [
                    'S1_136232_IW2_20200604T022312_VV_7C85-BURST',
                    'S1_136231_IW2_20200604T123455_VV_ABC5-BURST'
                ],
                'secondary': [
                    'S1_136231_IW2_20200617T022313_VV_5D11-BURST',
                    'S1_136233_IW2_20200617T123213_VV_5E13-BURST'
                ]
            }
        }
    ]
    invalid_jobs_duplicate = [
        {
            'job_parameters': {
                'reference': [
                    'S1_136231_IW2_20200604T022312_VV_7C85-BURST',
                    'S1_136231_IW2_20200604T123455_VV_ABC5-BURST'
                ],
                'secondary': [
                    'S1_136231_IW2_20200617T022313_VV_5D11-BURST',
                    'S1_136231_IW2_20200617T123213_VV_5E13-BURST'
                ]
            }
        },
        {
            'job_parameters': {
                'reference': [
                    'S1_136231_IW2_20200604T022312_VV_7C85-BURST',
                    'S1_136231_IW2_20200604T123455_VV_ABC5-BURST',
                    'S1_136232_IW2_20200604T125455_VV_ABC6-BURST',
                ],
                'secondary': [
                    'S1_136231_IW2_20200617T022313_VV_5D11-BURST',
                    'S1_136231_IW2_20200617T123213_VV_5E13-BURST',
                    'S1_136232_IW2_20200604T123475_VV_ABC7-BURST',
                ]
            }
        }
    ]
    for valid_job in valid_jobs:
        validation.check_same_burst_ids(valid_job, {})
    with raises(validation.GranuleValidationError, match=r'.*Number of reference and secondary scenes must match*'):
        validation.check_same_burst_ids(invalid_job_different_lengths, {})
    for invalid_job in invalid_jobs_not_matching:
        with raises(validation.GranuleValidationError, match=r'.*Burst IDs do not match*'):
            validation.check_same_burst_ids(invalid_job, {})
    for invalid_job in invalid_jobs_duplicate:
        with raises(validation.GranuleValidationError, match=r'.*The requested scenes have more than 1 pair*'):
            validation.check_same_burst_ids(invalid_job, {})


def test_check_valid_polarizations():
    valid_jobs = [
        {
            'job_parameters': {
                'reference': ['S1_136231_IW2_20200604T022312_VV_7C85-BURST'],
                'secondary': ['S1_136231_IW2_20200616T022313_VV_5D11-BURST']
            }
        },
        {
            'job_parameters': {
                'reference': [
                    'S1_136231_IW2_20200604T022312_HH_7C85-BURST',
                    'S1_136232_IW2_20200616T022315_HH_5D11-BURST'
                ],
                'secondary': [
                    'S1_136231_IW2_20200616T022313_HH_5411-BURST',
                    'S1_136232_IW2_20200616T022345_HH_5D13-BURST'
                ]
            }
        }
    ]
    invalid_jobs_not_matching = [
        {
            'job_parameters': {
                'reference': ['S1_136231_IW2_20200604T022312_VV_7C85-BURST'],
                'secondary': ['S1_136232_IW2_20200616T022313_HH_5D11-BURST']
            }
        },
        {
            'job_parameters': {
                'reference': [
                    'S1_136231_IW2_20200604T022312_VV_7C85-BURST',
                    'S1_136232_IW2_20200604T123455_VV_ABC5-BURST'
                ],
                'secondary': [
                    'S1_136231_IW2_20200617T022313_VV_5D11-BURST',
                    'S1_136233_IW2_20200617T123213_HH_5E13-BURST'
                ]
            }
        },
        {
            'job_parameters': {
                'reference': [
                    'S1_136232_IW2_20200604T022312_VV_7C85-BURST',
                    'S1_136231_IW2_20200604T123455_HH_ABC5-BURST'
                ],
                'secondary': [
                    'S1_136231_IW2_20200617T022313_VV_5D11-BURST',
                    'S1_136233_IW2_20200617T123213_HH_5E13-BURST'
                ]
            }
        }
    ]
    invalid_jobs_unsupported = [
        {
            'job_parameters': {
                'reference': ['S1_136231_IW2_20200604T022312_VH_7C85-BURST'],
                'secondary': ['S1_136231_IW2_20200617T022313_VH_5D11-BURST']
            }
        },
        {
            'job_parameters': {
                'reference': [
                    'S1_136231_IW2_20200604T022312_HV_7C85-BURST',
                    'S1_136231_IW2_20200604T123455_HV_ABC5-BURST',
                    'S1_136232_IW2_20200604T125455_HV_ABC6-BURST',
                ],
                'secondary': [
                    'S1_136231_IW2_20200617T022313_HV_5D11-BURST',
                    'S1_136231_IW2_20200617T123213_HV_5E13-BURST',
                    'S1_136232_IW2_20200604T123475_HV_ABC7-BURST',
                ]
            }
        }
    ]
    for valid_job in valid_jobs:
        validation.check_valid_polarizations(valid_job, {})
    for invalid_job in invalid_jobs_not_matching:
        with raises(validation.GranuleValidationError, match=r'.*need to have the same polarization*'):
            validation.check_valid_polarizations(invalid_job, {})
    for invalid_job in invalid_jobs_unsupported:
        with raises(validation.GranuleValidationError, match=r'.*currently supported*'):
            validation.check_valid_polarizations(invalid_job, {})


def test_check_granules_exist():
    granule_metadata = [
        {
            'name': 'scene1',
        },
        {
            'name': 'scene2',
        },
    ]

    validation.check_granules_exist([], granule_metadata)
    validation.check_granules_exist(['scene1'], granule_metadata)
    validation.check_granules_exist(['scene1', 'scene2'], granule_metadata)

    with raises(validation.GranuleValidationError) as e:
        validation.check_granules_exist(['scene1', 'scene2', 'scene3', 'scene4', 'S2_foo', 'LC08_bar', 'LC09_bar'],
                                        granule_metadata)
    assert 'S2_foo' not in str(e)
    assert 'LC08_bar' not in str(e)
    assert 'LC09_bar' not in str(e)
    assert 'scene1' not in str(e)
    assert 'scene2' not in str(e)
    assert 'scene3' in str(e)
    assert 'scene4' in str(e)


def test_is_third_party_granule():
    assert validation.is_third_party_granule('S2A_MSIL1C_20200627T150921_N0209_R025_T22WEB_20200627T170912')
    assert validation.is_third_party_granule('S2B_22WEB_20200612_0_L1C')
    assert validation.is_third_party_granule('LC08_L1TP_009011_20200820_20200905_02_T1')
    assert validation.is_third_party_granule('LO08_L1GT_043001_20201106_20201110_02_T2')
    assert validation.is_third_party_granule('LT08_L1GT_041001_20200125_20200925_02_T2')
    assert validation.is_third_party_granule('LC09_L1GT_215109_20220125_20220125_02_T2')
    assert validation.is_third_party_granule('LO09_L1GT_215109_20220210_20220210_02_T2')
    assert validation.is_third_party_granule('LT09_L1GT_215109_20220210_20220210_02_T2')
    assert not validation.is_third_party_granule('S1_249434_IW1_20230523T170733_VV_8850-BURST')
    assert not validation.is_third_party_granule('S1A_IW_SLC__1SSH_20150608T205059_20150608T205126_006287_0083E8_C4F0')
    assert not validation.is_third_party_granule('foo')


@responses.activate
def test_get_cmr_metadata():
    response_payload = {
        'feed': {
            'entry': [
                {
                    'producer_granule_id': 'foo',
                    'polygons': [["-31.4 25.0 -29.7 25.5 -29.5 24.6 -31.2 24.1 -31.4 25.0"]],
                },
                {
                    'title': 'bar',
                    'polygons': [["0 1 2 3 4 5 6 7 0 1"]],
                }
            ],
        },
    }
    responses.post(CMR_URL, json=response_payload)

    assert validation.get_cmr_metadata(['foo', 'bar', 'hello']) == [
        {
            'name': 'foo',
            'polygon': Polygon([[25.0, -31.4], [25.5, -29.7], [24.6, -29.5], [24.1, -31.2]]),
        },
        {
            'name': 'bar',
            'polygon': Polygon([[1, 0], [3, 2], [5, 4], [7, 6]]),
        },
    ]


def test_validate_jobs():
    unknown_granule = 'unknown'
    granule_with_dem_coverage = 'S1A_IW_SLC__1SSV_20150621T120220_20150621T120232_006471_008934_72D8'
    granule_without_dem_coverage = 'S1A_IW_GRDH_1SDV_20201219T222530_20201219T222555_035761_042F72_8378'

    valid_burst_pair = (
        'S1_136231_IW2_20200604T022312_VV_7C85-BURST',
        'S1_136231_IW2_20200616T022313_VV_5D11-BURST'
    )

    invalid_burst_pair = (
        'S1_136231_IW2_20200616T022313_VV_5D11-BURST',
        'S1_136232_IW2_20200604T022315_VV_7C85-BURST'
    )

    granule_polygon_pairs = [
        (granule_with_dem_coverage,
         [['13.705972 -91.927132 14.452647 -91.773392 14.888498 -94.065727 '
           '14.143632 -94.211563 13.705972 -91.927132']]),
        (granule_without_dem_coverage,
         [['37.796551 -68.331245 36.293144 -67.966415 36.69714 -65.129745 '
           '38.198883 -65.437325 37.796551 -68.331245']])
    ]
    setup_requests_mock_with_given_polygons(granule_polygon_pairs)

    jobs = [
        {
            'job_type': 'RTC_GAMMA',
            'job_parameters': {
                'granules': [granule_with_dem_coverage],
            }
        },
        {
            'job_type': 'RTC_GAMMA',
            'job_parameters': {
                'granules': [granule_with_dem_coverage],
                'dem_name': 'copernicus',
            }
        },
        {
            'job_type': 'INSAR_GAMMA',
            'job_parameters': {
                'granules': [granule_with_dem_coverage, granule_with_dem_coverage],
            }
        },
        {
            'job_type': 'AUTORIFT',
            'job_parameters': {
                'granules': [granule_with_dem_coverage, granule_without_dem_coverage],
            }
        },
        {
            'job_type': 'ARIA_RAIDER',
            'job_parameters': {}
        },
        {
            'job_type': 'INSAR_ISCE_MULTI_BURST',
            'job_parameters': {
                'reference': [valid_burst_pair[0]],
                'secondary': [valid_burst_pair[1]]
            }
        },
        {
            'job_type': 'INSAR_ISCE_BURST',
            'job_parameters': {
                'granules': [valid_burst_pair[0], valid_burst_pair[1]]
            }
        }
    ]
    validation.validate_jobs(jobs)

    jobs = [
        {
            'job_type': 'RTC_GAMMA',
            'job_parameters': {
                'granules': [unknown_granule],
            }
        }
    ]
    with raises(validation.GranuleValidationError):
        validation.validate_jobs(jobs)

    jobs = [
        {
            'job_type': 'RTC_GAMMA',
            'job_parameters': {
                'granules': [granule_without_dem_coverage],
            }
        }
    ]
    with raises(validation.GranuleValidationError):
        validation.validate_jobs(jobs)

    jobs = [
        {
            'job_type': 'INSAR_ISCE_MULTI_BURST',
            'job_parameters': {
                'reference': [invalid_burst_pair[0]],
                'secondary': [invalid_burst_pair[1]]
            }
        }
    ]
    with raises(validation.GranuleValidationError):
        validation.validate_jobs(jobs)

    jobs = [
        {
            'job_type': 'INSAR_ISCE_BURST',
            'job_parameters': {
                'granules': [invalid_burst_pair[0], invalid_burst_pair[1]]
            }
        }
    ]
    with raises(validation.GranuleValidationError):
        validation.validate_jobs(jobs)


def test_check_bounds_formatting():
    valid_jobs = [
        {'job_parameters': {'bounds': [-10, 0, 10, 10]}},
        {'job_parameters': {'bounds': [-180, -90, -170, -80]}},
        {'job_parameters': {'bounds': [170, 75, 180, 90]}},
        {'job_parameters': {'bounds': [0, 0, 0, 0]}}
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
    for valid_job in valid_jobs:
        validation.check_bounds_formatting(valid_job, {})
    for invalid_job in invalid_jobs_bad_order:
        with raises(validation.BoundsValidationError, match=r'.*Invalid order for bounds.*'):
            validation.check_bounds_formatting(invalid_job, {})
    for invalid_job in invalid_jobs_bad_values:
        with raises(validation.BoundsValidationError, match=r'.*Invalid lon/lat value(s)*'):
            validation.check_bounds_formatting(invalid_job, {})


def test_check_granules_intersecting_bounds():
    job_with_specified_bounds = {'job_parameters': {"bounds": [-10, 0, 10, 10]}}
    job_with_default_bounds = {'job_parameters': {'bounds': [0, 0, 0, 0]}}
    valid_granule_metadata = [
        {'name': 'intersects1', 'polygon': Polygon.from_bounds(-10.0, 0.0, 10.0, 10.0)},
        {'name': 'intersects2', 'polygon': Polygon.from_bounds(-9.0, -1.0, 20.0, 11.0)},
        {'name': 'intersects3', 'polygon': Polygon.from_bounds(0.0, 5.0, 15.0, 15.0)}
    ]
    invalid_granule_metadata = [
        {'name': 'intersects1', 'polygon': Polygon.from_bounds(-10.0, 0.0, 10.0, 10.0)},
        {'name': 'does_not_intersect1', 'polygon': Polygon.from_bounds(10.1, -10, 20.0, -0.1)},
        {'name': 'intersects2', 'polygon': Polygon.from_bounds(-9.0, -1.0, 20.0, 11.0)},
        {'name': 'does_not_intersect2', 'polygon': Polygon.from_bounds(-80.0, 20.0, -60.0, 90.0)},
        {'name': 'does_not_intersect3', 'polygon': Polygon.from_bounds(100.0, -50.0, 120.0, -0.1)},
    ]
    validation.check_granules_intersecting_bounds(job_with_specified_bounds, valid_granule_metadata)
    validation.check_granules_intersecting_bounds(job_with_default_bounds, valid_granule_metadata)
    error_pattern = r".*bounds: \['does_not_intersect1', 'does_not_intersect2', 'does_not_intersect3'\]*"
    with raises(validation.GranuleValidationError, match=error_pattern):
        validation.check_granules_intersecting_bounds(job_with_specified_bounds, invalid_granule_metadata)
    with raises(validation.GranuleValidationError, match=error_pattern):
        validation.check_granules_intersecting_bounds(job_with_default_bounds, invalid_granule_metadata)


def check_same_relative_orbits():
    valid_granule_metadata = [
        {'name': 'S1A_IW_RAW__0SDV_20201015T161622_20201015T161654_034809_040E95_AF3C'},
        {'name': 'S1A_IW_RAW__0SDV_20200816T161620_20200816T161652_033934_03EFCE_5730'},
        {'name': 'S1B_IW_RAW__0SDV_20200810T161537_20200810T161610_022863_02B66A_F7D7'},
        {'name': 'S1B_IW_RAW__0SDV_20200623T161535_20200623T161607_022163_02A10F_7FD6'}
    ]
    invalid_granule_metadata = valid_granule_metadata
    invalid_granule_metadata.append(
        {'name': 'S1B_IW_RAW__0SDV_20200623T161535_20200623T161607_012345_02A10F_7FD6'} # 23
    )
    validation.check_same_relative_orbits({}, valid_granule_metadata)
    error_pattern = r'.*23 is not 87.*'
    with raises(validation.GranuleValidationError, match=error_pattern):
        validation.check_same_relative_orbits({}, invalid_granule_metadata)
