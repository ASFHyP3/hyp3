import json
import os

import requests
from shapely.geometry import Polygon, shape

CMR_UMM_URL = 'https://cmr.earthdata.nasa.gov/search/granules.umm_json'


def get_granule_polygon(granule):
    cmr_parameters = {
        'producer_granule_id': granule,
        'provider': 'ASF',
        'short_name': [
            'SENTINEL-1A_SLC',
            'SENTINEL-1B_SLC',
        ],
    }
    response = requests.post(CMR_UMM_URL, data=cmr_parameters)
    response.raise_for_status()
    geometry = response.json()['items'][0]['umm']['SpatialExtent']['HorizontalSpatialDomain']['Geometry']
    points = geometry['GPolygons'][0]['Boundary']['Points']
    points_list = [[p['Longitude'], p['Latitude']] for p in points]
    return points_list


def get_coverage_shapes_from_geojson():
    demfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dem_coverage_map.geojson')
    with open(demfile) as f:
        shp = json.load(f)['features'][0]['geometry']
    return [x.buffer(0) for x in shape(shp).buffer(0).geoms]


def check_intersect(polygon: Polygon):
    coverage = get_coverage_shapes_from_geojson()
    for poly in coverage:
        if polygon.intersects(poly):
            return True
    return False
