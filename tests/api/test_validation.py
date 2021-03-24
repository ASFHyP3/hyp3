from pytest import raises
from shapely.geometry import Polygon

from hyp3_api import validation


def rectangle(north, south, east, west):
    return Polygon([[west, north], [east, north], [east, south], [west, south]])


def test_has_sufficient_coverage_cop30():
    # Wyoming
    poly = rectangle(45, 41, -104, -111)
    assert validation.has_sufficient_coverage_cop30(poly)

    # completely covers Aleutian Islands over antimeridian; should pass with fixed antimeridian
    poly = rectangle(51.7, 51.3, 179.7, -179.3)
    assert validation.has_sufficient_coverage_cop30(poly)

    # completely encloses tile over Ascension Island in the Atlantic
    poly = rectangle(-6, -9, -15, -14)
    assert validation.has_sufficient_coverage_cop30(poly)

    # # minimum sufficient coverage off the coast of Eureka, CA
    poly = rectangle(40.1, 40, -126, -125.000138)
    assert validation.has_sufficient_coverage_cop30(poly)

    # almost minimum sufficient coverage off the coast of Eureka, CA
    poly = rectangle(40.1, 40, -126, -125.000139)
    assert not validation.has_sufficient_coverage_cop30(poly)

    # polygon in missing tile over Gulf of California
    poly = rectangle(26.9, 26.1, -110.1, -110.9)
    assert not validation.has_sufficient_coverage_cop30(poly)

    # northern Greenland
    poly = rectangle(84.5, 83.5, -39, -40)
    assert validation.has_sufficient_coverage_cop30(poly)

    # Antarctica
    poly = rectangle(-89, -90, 180, -180)
    assert validation.has_sufficient_coverage_cop30(poly)

    # ocean over antimeridian; should FAIL with fixed antimeridian
    poly = rectangle(-40, -41, 179.7, -179.3)
    assert validation.has_sufficient_coverage_cop30(poly)


def test_has_sufficient_coverage_legacy():
    # Wyoming
    poly = rectangle(45, 41, -104, -111)
    assert validation.has_sufficient_coverage_legacy(poly)

    # completely covered Aleutian Islands over antimeridian; should pass with fixed antimeridian
    poly = rectangle(51.7, 51.3, 179.7, -179.3)
    assert validation.has_sufficient_coverage_legacy(poly)

    # not enough coverage of Aleutian Islands over antimeridian
    # NOTE: Passes today but should FAIL with antimeridian feature fix
    poly = rectangle(51.7, 41.3, 179.7, -179.3)
    assert validation.has_sufficient_coverage_legacy(poly)

    # completely encloses tile over Ascension Island in the Atlantic
    poly = rectangle(-6, -9, -15, -14)
    assert validation.has_sufficient_coverage_legacy(poly)

    # minimum sufficient coverage off the coast of Eureka, CA
    poly = rectangle(40.1, 40, -126, -124.845)
    assert validation.has_sufficient_coverage_legacy(poly)

    # almost minimum sufficient coverage off the coast of Eureka, CA
    poly = rectangle(40.1, 40, -126, -124.849)
    assert not validation.has_sufficient_coverage_legacy(poly)

    # polygon in missing tile over Gulf of Californa
    poly = rectangle(26.9, 26.1, -110.1, -110.9)
    assert not validation.has_sufficient_coverage_legacy(poly)

    # southern Greenland
    poly = rectangle(62, 61, -44, -45)
    assert not validation.has_sufficient_coverage_legacy(poly)

    # Antarctica
    poly = rectangle(-62, -90, 180, -180)
    assert not validation.has_sufficient_coverage_legacy(poly)

    # ocean over antimeridian; no dem coverage and also not enough wraparound land intersection
    poly = rectangle(-40, -41, 179.7, -179.3)
    assert not validation.has_sufficient_coverage_legacy(poly)


def test_has_sufficient_coverage_legacy_buffer():
    needs_buffer = rectangle(40.1, 40, -126, -124.845)
    assert validation.has_sufficient_coverage_legacy(needs_buffer)
    assert validation.has_sufficient_coverage_legacy(needs_buffer, buffer=0.16)
    assert not validation.has_sufficient_coverage_legacy(needs_buffer, buffer=0.14)


def test_has_sufficient_coverage_legacy_threshold():
    poly = rectangle(40.1, 40, -126, -124.845)
    assert validation.has_sufficient_coverage_legacy(poly)
    assert validation.has_sufficient_coverage_legacy(poly, threshold=0.19)
    assert not validation.has_sufficient_coverage_legacy(poly, threshold=0.21)


def test_format_points():
    point_string = '-31.43 25.04 -29.76 25.54 -29.56 24.66 -31.23 24.15 -31.43 25.04'
    assert validation.format_points(point_string) == [
        [25.04, -31.43],
        [25.54, -29.76],
        [24.66, -29.56],
        [24.15, -31.23],
        [25.04, -31.43]
    ]


def test_check_dem_coverage_legacy():
    good = {
        'name': 'good',
        'polygon': rectangle(45, 41, -104, -111),
    }

    bad = {
        'name': 'bad',
        'polygon': rectangle(-62, -90, 180, -180),
    }

    validation.check_dem_coverage_legacy([])

    validation.check_dem_coverage_legacy([good])

    with raises(validation.GranuleValidationError) as e:
        validation.check_dem_coverage_legacy([bad])
    assert 'bad' in str(e)

    with raises(validation.GranuleValidationError) as e:
        validation.check_dem_coverage_legacy([good, bad])
    assert 'bad' in str(e)
    assert 'good' not in str(e)


def test_check_dem_coverage():
    good = {
        'name': 'good',
        'polygon': rectangle(45, 41, -104, -111),
    }

    bad = {
        'name': 'bad',
        'polygon': rectangle(-20, -30, 70, 100),
    }

    validation.check_dem_coverage([])

    validation.check_dem_coverage([good])

    with raises(validation.GranuleValidationError) as e:
        validation.check_dem_coverage([bad])
    assert 'bad' in str(e)

    with raises(validation.GranuleValidationError) as e:
        validation.check_dem_coverage([good, bad])
    assert 'bad' in str(e)
    assert 'good' not in str(e)


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
        validation.check_granules_exist(['scene1', 'scene2', 'scene3', 'scene4', 'S2_foo', 'LC08_bar'],
                                        granule_metadata)
    assert 'S2_foo' not in str(e)
    assert 'LC08_bar' not in str(e)
    assert 'scene1' not in str(e)
    assert 'scene2' not in str(e)
    assert 'scene3' in str(e)
    assert 'scene4' in str(e)


def test_is_third_party_granule():
    assert validation.is_third_party_granule('S2A_MSIL1C_20200627T150921_N0209_R025_T22WEB_20200627T170912')
    assert validation.is_third_party_granule('S2B_22WEB_20200612_0_L1C')
    assert validation.is_third_party_granule('LC08_L1TP_009011_20200820_20200905_02_T1')
    assert not validation.is_third_party_granule('S1A_IW_SLC__1SSH_20150608T205059_20150608T205126_006287_0083E8_C4F0')
    assert not validation.is_third_party_granule('foo')


def test_get_cmr_metadata():
    granules = ['S1A_IW_SLC__1SSV_20150621T120220_20150621T120232_006471_008934_72D8', 'not a real granule']
    assert validation.get_cmr_metadata(granules) == [
        {
            'name': 'S1A_IW_SLC__1SSV_20150621T120220_20150621T120232_006471_008934_72D8',
            'polygon': Polygon([
                [-91.927132, 13.705972],
                [-91.773392, 14.452647],
                [-94.065727, 14.888498],
                [-94.211563, 14.143632],
                [-91.927132, 13.705972],
            ]),
        },
    ]


def test_validate_jobs():
    unknown_granule = 'unknown'
    granule_with_dem_coverage = 'S1A_IW_SLC__1SSV_20150621T120220_20150621T120232_006471_008934_72D8'
    granule_without_legacy_dem_coverage = 'S1A_IW_SLC__1SSH_20190326T081759_20190326T081831_026506_02F822_52F9'
    granule_without_dem_coverage = 'S1A_IW_GRDH_1SDV_20201219T222530_20201219T222555_035761_042F72_8378'

    jobs = [
        {
            'job_type': 'RTC_GAMMA',
            'job_parameters': {
                'granules': [granule_without_legacy_dem_coverage],
            }
        },
        {
            'job_type': 'INSAR_GAMMA',
            'job_parameters': {
                'granules': [granule_with_dem_coverage],
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
            'job_type': 'INSAR_GAMMA',
            'job_parameters': {
                'granules': [granule_without_legacy_dem_coverage],
            }
        }
    ]
    with raises(validation.GranuleValidationError):
        validation.validate_jobs(jobs)
