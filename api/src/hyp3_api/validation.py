import json
import os

import requests
from shapely.geometry import Polygon, shape

from hyp3_api import CMR_URL


class CmrError(Exception):
    pass


class DemError(Exception):
    pass


def validate_granules(granules):
    cmr_parameters = {
        'producer_granule_id': granules,
        'provider': 'ASF',
        'short_name': [
            'SENTINEL-1A_SLC',
            'SENTINEL-1B_SLC',
        ],
    }
    response = requests.post(CMR_URL, data=cmr_parameters)
    response.raise_for_status()
    check_granules_exist(granules, response.json())
    check_dem_coverage(response.json())


def check_granules_exist(granules, cmr_response):
    found_granules = [entry['producer_granule_id'] for entry in cmr_response['feed']['entry']]
    not_found_granules = set(granules) - set(found_granules)
    if not_found_granules:
        raise CmrError(f'Some requested scenes could not be found: {",".join(not_found_granules)}')


def check_dem_coverage(cmr_response):
    granules = [
        {
            'name': entry['producer_granule_id'],
            'polygon':Polygon(format_points(entry['polygons'][0][0]))
        } for entry in cmr_response['feed']['entry']
    ]
    coverage = get_coverage_shapes_from_geojson()
    bad_granules = [granule['name'] for granule in granules if not check_intersect(granule['polygon'], coverage)]
    if bad_granules:
        raise DemError(f'Some requested scenes do not have dem coverage: {",".join(bad_granules)}')


def format_points(point_string):
    converted_to_float = [float(x) for x in point_string.split(' ')]
    points = [list(t) for t in zip(converted_to_float[1::2], converted_to_float[::2])]
    return points


def get_coverage_shapes_from_geojson():
    dem_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dem_coverage_map.geojson')
    with open(dem_file) as f:
        shp = json.load(f)['features'][0]['geometry']
    return [x.buffer(0) for x in shape(shp).buffer(0).geoms]


def check_intersect(granule: Polygon, coverage: list):
    for polygon in coverage:
        if granule.intersects(polygon):
            return True
    return False
