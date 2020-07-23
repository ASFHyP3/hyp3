from shapely.geometry import Polygon

from hyp3_api.validation import check_dem_coverage

def test_dem_validation_intersections():
    polygons = [
        {  # Checks inland polygon
            'shape': Polygon(
                [[-112.217865, 40.589935], [-111.80838, 38.969978], [-108.877068, 39.369526], [-109.213676, 40.98851],
                 [-112.217865, 40.589935]]),
            'intersects_coverage': True,
        },
        {  # Checks island polygon
            'shape': Polygon(
                [[168.840698, 53.818138], [169.488266, 55.596813], [165.534683, 55.997574], [165.060516, 54.214031],
                 [168.840698, 53.818138]]),
            'intersects_coverage': True,
        },
        {  # Checks polygon over land on international dateline
            'shape': Polygon(
                [[-168.355133, 63.74361], [-167.437805, 65.333801], [-172.817642, 65.79171], [-173.428421, 64.18708],
                 [-168.355133, 63.74361]]),
            'intersects_coverage': True,
        },
        {  # Checks polygon over water on international dateline
            'shape': Polygon(
                [[-169.842026, 60.806404], [-169.061523, 62.402794], [-173.905548, 62.836201], [-174.439957, 61.229523],
                 [-169.842026, 60.806404]]),
            'intersects_coverage': False,
        },
        {  # Checks polygon slightly missing dem coverage
            'shape': Polygon(
                [[-21.174782, 62.767269], [-20.375685, 61.171268], [-15.655336, 61.604073], [-16.198036, 63.211052],
                 [-21.174782, 62.767269]]),
            'intersects_coverage': False,
        },
    ]
    for polygon in polygons:
        result = check_dem_coverage(polygon['shape'])
        assert result == polygon['intersects_coverage']
