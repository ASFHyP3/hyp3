from pytest import raises
from shapely.geometry import Polygon


from hyp3_api.validation import GranuleValidationError, check_granules_for_dem_coverage, has_sufficient_coverage


def nsew(north, south, east, west):
    return Polygon([[west, north], [east, north], [east, south], [west, south]])


def test_check_dem_coverage():
    polygons = [
        {  # Wyoming
            'polygon': nsew(45, 41, -104, -111),
            'name': 'good1',
        },
        {  # completely covered Aleutian Islands over antimeridian; should pass with fixed antimeridian
            'polygon': nsew(51.7, 51.3, 179.7, -179.3),
            'name': 'good2',
        },
        {  # not enough coverage of Aleutian Islands over antimeridian
            # NOTE: Passes today but should FAIL with antimeridian feature fix
            'polygon': nsew(51.7, 41.3, 179.7, -179.3),
            'name': 'good3',
        },
        {  # completely encloses tile over Ascension Island in the Atlantic
            'polygon': nsew(-6, -9, -15, -14),
            'name': 'good4',
        },
        {  # minimum intersects off the coast of Eureka, CA
            'polygon': nsew(40.1, 40, -126, -124.845),
            'name': 'good5',
        },
        {  # almost minimum intersects off the coast of Eureka, CA
            'polygon': nsew(40.1, 40, -126, -124.849),
            'name': 'bad1',
        },
        {  # barely intersects off the coast of Eureka, CA
            'polygon': nsew(40.1, 40, -126, -125.00166),
            'name': 'bad2',
        },
        {  # barely misses off the coast of Eureka, CA
            'polygon': nsew(40.1, 40, -126, -125.00167),
            'name': 'bad3',
        },
        {  # polygon in missing tile over Gulf of Californa
            'polygon': nsew(26.9, 26.1, -110.1, -110.9),
            'name': 'bad4',
        },
        {  # southern Greenland
            'polygon': nsew(62, 61, -44, -45),
            'name': 'bad5',
        },
        {  # Antarctica
            'polygon': nsew(-62, -90, 180, -180),
            'name': 'bad6',
        },
        {  # ocean over antimeridian; no dem coverage and also not enough wraparound land intersection
            'polygon': nsew(-40, -41, 179.7, -179.3),
            'name': 'bad7',
        },
    ]
    with raises(GranuleValidationError) as exception_info:
        check_granules_for_dem_coverage(polygons)
    for polygon in polygons:
        assert polygon['name'].startswith('bad') == (polygon['name'] in str(exception_info))


def test_has_sufficient_coverage_buffer():
    needs_buffer = nsew(40.1, 40, -126, -124.845)
    assert has_sufficient_coverage(needs_buffer)
    assert has_sufficient_coverage(needs_buffer, buffer=0.16)
    assert not has_sufficient_coverage(needs_buffer, buffer=0.14)


def test_has_sufficient_coverage_threshold():
    poly = nsew(40.1, 40, -126, -124.845)
    assert has_sufficient_coverage(poly)
    assert has_sufficient_coverage(poly, threshold=0.19)
    assert not has_sufficient_coverage(poly, threshold=0.21)
