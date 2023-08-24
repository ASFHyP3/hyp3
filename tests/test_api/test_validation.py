import responses
from pytest import raises
from shapely.geometry import Polygon
from test_api.conftest import setup_requests_mock_with_given_polygons

from hyp3_api import CMR_URL, validation


def rectangle(north, south, east, west):
    return Polygon([[west, north], [east, north], [east, south], [west, south]])


def test_has_sufficient_coverage():
    # Wyoming
    poly = rectangle(45, 41, -104, -111)
    assert validation.has_sufficient_coverage(poly)
    assert validation.has_sufficient_coverage(poly, legacy=True)

    # completely covered Aleutian Islands over antimeridian; should pass with fixed antimeridian
    poly = rectangle(51.7, 51.3, 179.7, -179.3)
    assert validation.has_sufficient_coverage(poly)
    assert validation.has_sufficient_coverage(poly, legacy=True)

    # not enough coverage of Aleutian Islands over antimeridian
    # NOTE: Passes today but should FAIL legacy with antimeridian feature fix
    poly = rectangle(51.7, 41.3, 179.7, -179.3)
    assert validation.has_sufficient_coverage(poly)
    assert validation.has_sufficient_coverage(poly, legacy=True)

    # completely encloses tile over Ascension Island in the Atlantic
    poly = rectangle(-6, -9, -15, -14)
    assert validation.has_sufficient_coverage(poly)
    assert validation.has_sufficient_coverage(poly, legacy=True)

    # # minimum sufficient coverage off the coast of Eureka, CA
    poly = rectangle(40.1, 40, -126, -125.000138)
    assert validation.has_sufficient_coverage(poly)
    assert not validation.has_sufficient_coverage(poly, legacy=True)

    # almost minimum sufficient coverage off the coast of Eureka, CA
    poly = rectangle(40.1, 40, -126, -125.000140)
    assert not validation.has_sufficient_coverage(poly)
    assert not validation.has_sufficient_coverage(poly, legacy=True)

    # minimum sufficient legacy coverage off the coast of Eureka, CA
    poly = rectangle(40.1, 40, -126, -124.845)
    assert validation.has_sufficient_coverage(poly)
    assert validation.has_sufficient_coverage(poly, legacy=True)

    # almost minimum sufficient legacy coverage off the coast of Eureka, CA
    poly = rectangle(40.1, 40, -126, -124.849)
    assert validation.has_sufficient_coverage(poly)
    assert not validation.has_sufficient_coverage(poly, legacy=True)

    # polygon in missing tile over Gulf of California
    poly = rectangle(26.9, 26.1, -110.1, -110.9)
    assert not validation.has_sufficient_coverage(poly)
    assert not validation.has_sufficient_coverage(poly, legacy=True)

    # southern Greenland
    poly = rectangle(62, 61, -44, -45)
    assert validation.has_sufficient_coverage(poly)
    assert not validation.has_sufficient_coverage(poly, legacy=True)

    # Antarctica
    poly = rectangle(-62, -90, 180, -180)
    assert validation.has_sufficient_coverage(poly)
    assert not validation.has_sufficient_coverage(poly, legacy=True)

    # ocean over antimeridian; no dem coverage and also not enough legacy wraparound land intersection
    # should FAIL with legacy with antimeridian feature fix
    poly = rectangle(-40, -41, 179.7, -179.3)
    assert validation.has_sufficient_coverage(poly)
    assert not validation.has_sufficient_coverage(poly, legacy=True)


def test_has_sufficient_coverage_legacy_buffer():
    needs_buffer = rectangle(40.1, 40, -126, -124.845)
    assert validation.has_sufficient_coverage(needs_buffer, legacy=True)
    assert validation.has_sufficient_coverage(needs_buffer, buffer=0.16, legacy=True)
    assert not validation.has_sufficient_coverage(needs_buffer, buffer=0.14, legacy=True)


def test_has_sufficient_coverage_legacy_threshold():
    poly = rectangle(40.1, 40, -126, -124.845)
    assert validation.has_sufficient_coverage(poly, legacy=True)
    assert validation.has_sufficient_coverage(poly, threshold=0.19, legacy=True)
    assert not validation.has_sufficient_coverage(poly, threshold=0.21, legacy=True)


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
    both = {'name': 'both', 'polygon': rectangle(45, 41, -104, -111)}
    copernicus_only = {'name': 'copernicus_only', 'polygon': rectangle(-62, -90, 180, -180)}
    neither = {'name': 'neither', 'polygon': rectangle(-20, -30, 70, 100)}

    job = {'job_type': 'RTC_GAMMA', 'job_parameters': {'dem_name': 'copernicus'}}
    validation.check_dem_coverage(job, [])
    validation.check_dem_coverage(job, [both])
    validation.check_dem_coverage(job, [copernicus_only])

    with raises(validation.GranuleValidationError) as e:
        validation.check_dem_coverage(job, [neither])
    assert 'neither' in str(e)

    with raises(validation.GranuleValidationError) as e:
        validation.check_dem_coverage(job, [copernicus_only, neither])
    assert 'neither' in str(e)
    assert 'copernicus_only' not in str(e)

    job = {'job_type': 'RTC_GAMMA', 'job_parameters': {'dem_name': 'legacy'}}
    validation.check_dem_coverage(job, [both])

    with raises(validation.GranuleValidationError):
        validation.check_dem_coverage(job, [copernicus_only])

    with raises(validation.GranuleValidationError):
        validation.check_dem_coverage(job, [neither])

    job = {'job_type': 'RTC_GAMMA', 'job_parameters': {}}
    validation.check_dem_coverage(job, [both])
    validation.check_dem_coverage(job, [copernicus_only])

    with raises(validation.GranuleValidationError):
        validation.check_dem_coverage(job, [neither])

    job = {'job_type': 'INSAR_GAMMA', 'job_parameters': {}}
    validation.check_dem_coverage(job, [both])
    validation.check_dem_coverage(job, [copernicus_only])

    with raises(validation.GranuleValidationError):
        validation.check_dem_coverage(job, [neither])


def test_check_same_burst_ids():
    valid_case = [
        {
            'name': 'S1_136231_IW2_20200604T022312_VV_7C85-BURST'
        },
        {
            'name': 'S1_136231_IW2_20200616T022313_VV_5D11-BURST'
        }
    ]
    invalid_case = [
        {
            'name': 'S1_136231_IW2_20200604T022312_VV_7C85-BURST'
        },
        {
            'name': 'S1_136232_IW2_20200616T022313_HH_5D11-BURST'
        }
    ]

    validation.check_same_burst_ids('', valid_case)
    with raises(validation.GranuleValidationError, match=r'.*do not have the same burst id.*'):
        validation.check_same_burst_ids('', invalid_case)


def test_check_valid_polarizations():
    valid_case = [
        {
            'name': 'S1_136231_IW2_20200604T022312_VV_7C85-BURST'
        },
        {
            'name': 'S1_136231_IW2_20200616T022313_VV_5D11-BURST'
        }
    ]
    different_polarizations = [
        {
            'name': 'S1_136231_IW2_20200604T022312_VV_7C85-BURST'
        },
        {
            'name': 'S1_136231_IW2_20200616T022313_HH_5D11-BURST'
        }
    ]
    unsupported_polarizations = [
        {
            'name': 'S1_136231_IW2_20200604T022312_VH_7C85-BURST'
        },
        {
            'name': 'S1_136231_IW2_20200616T022313_VH_5D11-BURST'
        }
    ]

    validation.check_valid_polarizations('', valid_case)
    with raises(validation.GranuleValidationError, match=r'.*do not have the same polarization.*'):
        validation.check_valid_polarizations('', different_polarizations)
    with raises(validation.GranuleValidationError, match=r'.*Only VV and HH.*'):
        validation.check_valid_polarizations('', unsupported_polarizations)


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
    granule_without_legacy_dem_coverage = 'S1A_IW_SLC__1SSH_20190326T081759_20190326T081831_026506_02F822_52F9'
    granule_without_dem_coverage = 'S1A_IW_GRDH_1SDV_20201219T222530_20201219T222555_035761_042F72_8378'

    granule_polygon_pairs = [
        (granule_with_dem_coverage,
         [['13.705972 -91.927132 14.452647 -91.773392 14.888498 -94.065727 '
           '14.143632 -94.211563 13.705972 -91.927132']]),
        (granule_without_legacy_dem_coverage,
         [['-66.116837 -61.940685 -64.415421 -59.718628 -63.285854 -64.154266 '
           '-64.918007 -66.566696 -66.116837 -61.940685']]),
        (granule_without_dem_coverage,
         [['37.796551 -68.331245 36.293144 -67.966415 36.69714 -65.129745 '
           '38.198883 -65.437325 37.796551 -68.331245']])
    ]
    setup_requests_mock_with_given_polygons(granule_polygon_pairs)

    jobs = [
        {
            'job_type': 'RTC_GAMMA',
            'job_parameters': {
                'granules': [granule_without_legacy_dem_coverage],
            }
        },
        {
            'job_type': 'RTC_GAMMA',
            'job_parameters': {
                'granules': [granule_without_legacy_dem_coverage],
                'dem_name': 'copernicus',
            }
        },
        {
            'job_type': 'RTC_GAMMA',
            'job_parameters': {
                'granules': [granule_with_dem_coverage],
                'dem_name': 'legacy',
            }
        },
        {
            'job_type': 'INSAR_GAMMA',
            'job_parameters': {
                'granules': [granule_with_dem_coverage, granule_without_legacy_dem_coverage],
            }
        },
        {
            'job_type': 'AUTORIFT',
            'job_parameters': {
                'granules': [granule_with_dem_coverage, granule_without_dem_coverage],
            }
        },
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
