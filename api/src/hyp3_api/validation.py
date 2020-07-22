import json
import os

import requests
from shapely.geometry import Polygon, shape

from hyp3_api import CMR_URL


class CmrError(Exception):
    pass


def check_granules_exist(granules):
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
    found_granules = [entry['producer_granule_id'] for entry in response.json()['feed']['entry']]
    not_found_granules = set(granules) - set(found_granules)
    if not_found_granules:
        raise CmrError(f'Some requested scenes could not be found: {",".join(not_found_granules)}')


def get_granule_polygon(granule):
    cmr_parameters = {
        'producer_granule_id': granule,
        'provider': 'ASF',
        'short_name': [
            'SENTINEL-1A_SLC',
            'SENTINEL-1B_SLC',
        ],
    }
    response = requests.post(CMR_URL, data=cmr_parameters)
    response.raise_for_status()
    points_string = response.json()['feed']['entry'][0]['polygons'][0][0]
    points_list = [float(a) for a in points_string.split(' ')]
    points = [list(t) for t in zip(points_list[1::2], points_list[::2])]
    return Polygon(points)


def get_coverage_shapes_from_geojson():
    dem_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dem_coverage_map.geojson')
    with open(dem_file) as f:
        shp = json.load(f)['features'][0]['geometry']
    return [x.buffer(0) for x in shape(shp).buffer(0).geoms]


def check_intersect(polygon: Polygon):
    coverage = get_coverage_shapes_from_geojson()
    for poly in coverage:
        if polygon.intersects(poly):
            return True
    return False
