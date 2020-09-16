import json
import os

import requests
from shapely.geometry import MultiPolygon, Polygon, shape

from hyp3_api import CMR_URL
from hyp3_api.util import get_granules

DEM_COVERAGE = None


class GranuleValidationError(Exception):
    pass


def has_sufficient_coverage(granule: Polygon, buffer: float = 0.15, threshold: float = 0.2):
    global DEM_COVERAGE
    if DEM_COVERAGE is None:
        DEM_COVERAGE = MultiPolygon(get_coverage_shapes_from_geojson())

    buffered_granule = granule.buffer(buffer)
    covered_area = buffered_granule.intersection(DEM_COVERAGE).area

    return covered_area / buffered_granule.area >= threshold


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


def check_granules_exist(job, granule_metadata):
    found_granules = [granule['name'] for granule in granule_metadata]
    not_found_granules = set(get_granules([job])) - set(found_granules)
    if not_found_granules:
        raise GranuleValidationError(f'Some requested scenes could not be found: {", ".join(not_found_granules)}')


def check_granules_for_dem_coverage(granules):
    bad_granules = [granule['name'] for granule in granules if not has_sufficient_coverage(granule['polygon'])]
    if bad_granules:
        raise GranuleValidationError(f'Some requested scenes do not have DEM coverage: {", ".join(bad_granules)}')


def check_dem_coverage(job, granule_metadata):
    granules_to_check = [granule for granule in granule_metadata if granule['name'] in get_granules([job])]
    check_granules_for_dem_coverage(granules_to_check)


def format_points(point_string):
    converted_to_float = [float(x) for x in point_string.split(' ')]
    points = [list(t) for t in zip(converted_to_float[1::2], converted_to_float[::2])]
    return points


def get_coverage_shapes_from_geojson():
    dem_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dem_coverage_map.geojson')
    with open(dem_file) as f:
        shp = json.load(f)['features'][0]['geometry']
    return [x.buffer(0) for x in shape(shp).buffer(0).geoms]


def validate_jobs(jobs):
    job_validation_map = {
        'RTC_GAMMA': [
            check_granules_exist,
            check_dem_coverage,
        ],
        'INSAR_GAMMA': [
            check_granules_exist,
            check_dem_coverage,
        ],
        'AUTORIFT': [
            check_granules_exist,
        ]
    }
    granules = get_granules(jobs)
    granule_metadata = get_cmr_metadata(granules)

    for job in jobs:
        for validator in job_validation_map[job['job_type']]:
            validator(job, granule_metadata)
