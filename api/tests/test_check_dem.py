from pytest import raises
from shapely.geometry import Polygon


from hyp3_api.validation import GranuleValidationError, check_dem_coverage


def nsew(north, south, east, west):
    return Polygon([[west, north], [east, north], [east, south], [west, south]])


def test_check_dem_coverage():
    polygons = [
        {  # Wyoming
            'polygon': nsew(45, 41, -104, -111),
            'name': 'good1',
        },
        {  # Alluetean Islands over antimeridian
            'polygon': nsew(51.7, 51.3, 179.7, -179.3),
            'name': 'good2',
        },
        {  # ocean over antimeridian; no dem coverage but we expect to pass validation
            'polygon': nsew(-40, -41, 179.7, -179.3),
            'name': 'good3',
        },
        {  # completely encloses tile over Ascension Island in the Atlantic
            'polygon': nsew(-6, -9, -16, -13),
            'name': 'good4',
        },
        {  # barely intersects off the coast of Eureka, CA
            'polygon': nsew(40.1, 40, -126, -125.00166),
            'name': 'good5',
        },
        {  # barely misses off the coast of Eureka, CA
            'polygon': nsew(40.1, 40, -126, -125.00167),
            'name': 'bad1',
        },
        {  # polygon in missing tile over Gulf of Californa
            'polygon': nsew(26.9, 26.1, -110.1, -110.9),
            'name': 'bad2',
        },
        {  # southern Greenland
            'polygon': nsew(62, 61, -44, -45),
            'name': 'bad3',
        },
        {  # Antarctica
            'polygon': nsew(-62, -90, 180, -180),
            'name': 'bad4',
        },
    ]
    with raises(GranuleValidationError) as exception_info:
        check_dem_coverage(polygons)
    for polygon in polygons:
        assert polygon['name'].startswith('bad') == (polygon['name'] in str(exception_info))
