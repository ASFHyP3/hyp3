from pytest import raises
from shapely.geometry import Polygon

from hyp3_api.validation import GranuleValidationError, check_dem_coverage, check_granules_exist, format_points, \
    get_cmr_metadata, has_sufficient_coverage, validate_jobs


def rectangle(north, south, east, west):
    return Polygon([[west, north], [east, north], [east, south], [west, south]])


def test_has_sufficient_coverage():
    # Wyoming
    poly = rectangle(45, 41, -104, -111)
    assert has_sufficient_coverage(poly)

    # completely covered Aleutian Islands over antimeridian; should pass with fixed antimeridian
    poly = rectangle(51.7, 51.3, 179.7, -179.3)
    assert has_sufficient_coverage(poly)

    # not enough coverage of Aleutian Islands over antimeridian
    # NOTE: Passes today but should FAIL with antimeridian feature fix
    poly = rectangle(51.7, 41.3, 179.7, -179.3)
    assert has_sufficient_coverage(poly)

    # completely encloses tile over Ascension Island in the Atlantic
    poly = rectangle(-6, -9, -15, -14)
    assert has_sufficient_coverage(poly)

    # minimum sufficient coverage off the coast of Eureka, CA
    poly = rectangle(40.1, 40, -126, -124.845)
    assert has_sufficient_coverage(poly)

    # almost minimum sufficient coverage off the coast of Eureka, CA
    poly = rectangle(40.1, 40, -126, -124.849)
    assert not has_sufficient_coverage(poly)

    # polygon in missing tile over Gulf of Californa
    poly = rectangle(26.9, 26.1, -110.1, -110.9)
    assert not has_sufficient_coverage(poly)

    # southern Greenland
    poly = rectangle(62, 61, -44, -45)
    assert not has_sufficient_coverage(poly)

    # Antarctica
    poly = rectangle(-62, -90, 180, -180)
    assert not has_sufficient_coverage(poly)

    # ocean over antimeridian; no dem coverage and also not enough wraparound land intersection
    poly = rectangle(-40, -41, 179.7, -179.3)
    assert not has_sufficient_coverage(poly)


def test_has_sufficient_coverage_buffer():
    needs_buffer = rectangle(40.1, 40, -126, -124.845)
    assert has_sufficient_coverage(needs_buffer)
    assert has_sufficient_coverage(needs_buffer, buffer=0.16)
    assert not has_sufficient_coverage(needs_buffer, buffer=0.14)


def test_has_sufficient_coverage_threshold():
    poly = rectangle(40.1, 40, -126, -124.845)
    assert has_sufficient_coverage(poly)
    assert has_sufficient_coverage(poly, threshold=0.19)
    assert not has_sufficient_coverage(poly, threshold=0.21)


def test_format_points():
    point_string = '-31.43 25.04 -29.76 25.54 -29.56 24.66 -31.23 24.15 -31.43 25.04'
    assert format_points(point_string) == [
        [25.04, -31.43],
        [25.54, -29.76],
        [24.66, -29.56],
        [24.15, -31.23],
        [25.04, -31.43]
    ]


def test_check_dem_coverage():
    good = {
        'name': 'good',
        'polygon': rectangle(45, 41, -104, -111),
    }

    bad = {
        'name': 'bad',
        'polygon': rectangle(-62, -90, 180, -180),
    }

    check_dem_coverage([])

    check_dem_coverage([good])

    with raises(GranuleValidationError) as e:
        check_dem_coverage([bad])
    assert 'bad' in str(e)

    with raises(GranuleValidationError) as e:
        check_dem_coverage([good, bad])
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

    check_granules_exist([], granule_metadata)
    check_granules_exist(['scene1'], granule_metadata)
    check_granules_exist(['scene1', 'scene2'], granule_metadata)

    with raises(GranuleValidationError) as e:
        check_granules_exist(['scene1', 'scene2', 'scene3', 'scene4'], granule_metadata)
    assert 'scene1' not in str(e)
    assert 'scene2' not in str(e)
    assert 'scene3' in str(e)
    assert 'scene4' in str(e)


def test_get_cmr_metadata():
    granules = ['S1A_IW_SLC__1SSV_20150621T120220_20150621T120232_006471_008934_72D8', 'not a real granule']
    assert get_cmr_metadata(granules) == [
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
    granule_without_dem_coverage = 'S1A_IW_SLC__1SSH_20190326T081759_20190326T081831_026506_02F822_52F9'

    jobs = [
        {
            'job_type': 'RTC_GAMMA',
            'job_parameters': {
                'granules': [granule_with_dem_coverage],
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
    validate_jobs(jobs)

    jobs = [
        {
            'job_type': 'RTC_GAMMA',
            'job_parameters': {
                'granules': [unknown_granule],
            }
        }
    ]
    with raises(GranuleValidationError):
        validate_jobs(jobs)

    jobs = [
        {
            'job_type': 'INSAR_GAMMA',
            'job_parameters': {
                'granules': [granule_without_dem_coverage],
            }
        }
    ]
    with raises(GranuleValidationError):
        validate_jobs(jobs)
