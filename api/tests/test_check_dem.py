from pytest import raises
from shapely.geometry import Polygon


from hyp3_api.validation import GranuleValidationError, check_dem_coverage


def test_dem_validation_intersections():
    polygons = [
        {  # Checks inland polygon
            'polygon': Polygon(
                [[-112.217865, 40.589935], [-111.80838, 38.969978], [-108.877068, 39.369526], [-109.213676, 40.98851],
                 [-112.217865, 40.589935]]),
            'name': 'good1',
        },
        {  # Checks island polygon
            'polygon': Polygon(
                [[168.840698, 53.818138], [169.488266, 55.596813], [165.534683, 55.997574], [165.060516, 54.214031],
                 [168.840698, 53.818138]]),
            'name': 'good2',
        },
        {  # Checks polygon over land on international dateline
            'polygon': Polygon(
                [[-168.355133, 63.74361], [-167.437805, 65.333801], [-172.817642, 65.79171], [-173.428421, 64.18708],
                 [-168.355133, 63.74361]]),
            'name': 'good3',
        },
        {  # Checks polygon over water on international dateline
            'polygon': Polygon(
                [[-169.842026, 60.806404], [-169.061523, 62.402794], [-173.905548, 62.836201], [-174.439957, 61.229523],
                 [-169.842026, 60.806404]]),
            'name': 'bad1',
        },
        {  # Checks polygon slightly missing dem coverage
            'polygon': Polygon(
                [[-21.174782, 62.767269], [-20.375685, 61.171268], [-15.655336, 61.604073], [-16.198036, 63.211052],
                 [-21.174782, 62.767269]]),
            'name': 'bad2',
        },
    ]
    with raises(GranuleValidationError) as exception_info:
        check_dem_coverage(polygons)
    for name in ['bad1', 'bad2']:
        assert name in str(exception_info)
    for name in ['good1', 'good2', 'good3']:
        assert name not in str(exception_info)
