import json
import os

import requests
from shapely.geometry import Polygon, shape

from hyp3_api import CMR_URL

DEM_COVERAGE = None


class GranuleValidationError(Exception):
    pass


def check_intersects_with_coverage(granule: Polygon):
    global DEM_COVERAGE
    if DEM_COVERAGE is None:
        DEM_COVERAGE = get_coverage_shapes_from_geojson()
    for polygon in DEM_COVERAGE:
        if granule.intersects(polygon):
            return True
    return False


def validate_granules(granules):
    granule_metadata = get_cmr_metadata(granules)

    check_granules_exist(granules, granule_metadata)
    check_dem_coverage(granule_metadata)


def get_cmr_metadata(granules):
    cmr_parameters = {
        'producer_granule_id': granules,
        'provider': 'ASF',
        'short_name': [
            'SENTINEL-1A_SLC',
            'SENTINEL-1B_SLC',
            'SENTINEL-1A_SP_GRD_HIGH',
            'SENTINEL-1B_SP_GRD_HIGH',
            'SENTINEL-1A_DP_GRD_HIGH',
            'SENTINEL-1B_DP_GRD_HIGH',
        ],
        'page_size': 2000,
    }
    response = requests.post(CMR_URL, data=cmr_parameters)
    response.raise_for_status()
    granules = [
        {
            'name': entry['producer_granule_id'],
            'polygon': Polygon(format_points(entry['polygons'][0][0]))
        } for entry in response.json()['feed']['entry']
    ]
    return granules


def check_granules_exist(granules, granule_metadata):
    found_granules = [granule['name'] for granule in granule_metadata]
    not_found_granules = set(granules) - set(found_granules)
    if not_found_granules:
        raise GranuleValidationError(f'Some requested scenes could not be found: {", ".join(not_found_granules)}')


def check_dem_coverage(granule_metadata):
    bad_granules = {granule['name'] for granule in granule_metadata if
                    not check_intersects_with_coverage(granule['polygon'])}
    if bad_granules:
        raise GranuleValidationError(f'Some requested scenes do not have DEM coverage: {", ".join(bad_granules)}')


def format_points(point_string):
    converted_to_float = [float(x) for x in point_string.split(' ')]
    points = [list(t) for t in zip(converted_to_float[1::2], converted_to_float[::2])]
    return points


def get_coverage_shapes_from_geojson():
    dem_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dem_coverage_map.geojson')
    with open(dem_file) as f:
        shp = json.load(f)['features'][0]['geometry']
    return [x.buffer(0) for x in shape(shp).buffer(0).geoms]
