import json
import os
import sys
from pathlib import Path

import requests
import yaml
from shapely.geometry import MultiPolygon, Polygon, shape

from hyp3_api import CMR_URL
from hyp3_api.util import get_granules

DEM_COVERAGE = None


class GranuleValidationError(Exception):
    pass


with open(Path(__file__).parent / 'job_validation_map.yml') as f:
    JOB_VALIDATION_MAP = yaml.safe_load(f.read())


def has_sufficient_coverage(granule: Polygon):
    global DEM_COVERAGE
    if DEM_COVERAGE is None:
        DEM_COVERAGE = get_multipolygon_from_geojson('dem_coverage_map_cop30.geojson')

    return granule.intersects(DEM_COVERAGE)


def get_cmr_metadata(granules):
    cmr_parameters = {
        'granule_ur': [f'{granule}*' for granule in granules],
        'options[granule_ur][pattern]': 'true',
        'provider': 'ASF',
        'short_name': [
            'SENTINEL-1A_SLC',
            'SENTINEL-1B_SLC',
            'SENTINEL-1A_SP_GRD_HIGH',
            'SENTINEL-1B_SP_GRD_HIGH',
            'SENTINEL-1A_DP_GRD_HIGH',
            'SENTINEL-1B_DP_GRD_HIGH',
            'SENTINEL-1_BURSTS',
            'SENTINEL-1A_RAW',
            'SENTINEL-1B_RAW',
        ],
        'page_size': 2000,
    }
    response = requests.post(CMR_URL, data=cmr_parameters)
    response.raise_for_status()
    granules = [
        {
            'name': entry.get('producer_granule_id', entry.get('title')),
            'polygon': Polygon(format_points(entry['polygons'][0][0]))
        } for entry in response.json()['feed']['entry']
    ]
    return granules


def is_third_party_granule(granule):
    return granule.startswith('S2') or granule.startswith('L')


def check_granules_exist(granules, granule_metadata):
    found_granules = [granule['name'] for granule in granule_metadata]
    not_found_granules = set(granules) - set(found_granules)
    not_found_granules = {granule for granule in not_found_granules if not is_third_party_granule(granule)}
    if not_found_granules:
        raise GranuleValidationError(f'Some requested scenes could not be found: {", ".join(not_found_granules)}')


def check_dem_coverage(granule_metadata):
    bad_granules = [g['name'] for g in granule_metadata if not has_sufficient_coverage(g['polygon'])]
    if bad_granules:
        raise GranuleValidationError(f'Some requested scenes do not have DEM coverage: {", ".join(bad_granules)}')


def check_same_burst_ids(granule_metadata):
    burst_ids = [granule['name'].split('_')[1] for granule in granule_metadata]
    not_matching = [burst_id for burst_id in set(burst_ids) if burst_ids.count(burst_id) == 1]
    if not_matching:
        raise GranuleValidationError(
            f'The requests scenes have burst IDs with no matching pairs: {not_matching}.'
        )


def check_valid_polarizations(granule_metadata):
    polarizations = set(granule['name'].split('_')[4] for granule in granule_metadata)
    if len(polarizations) > 1:
        raise GranuleValidationError(
            f'The requested scenes need to have the same polarization, got: {", ".join(polarizations)}'
        )
    if not polarizations.issubset({'VV', 'HH'}):
        raise GranuleValidationError(
            f'Only VV and HH polarizations are currently supported, got: {polarizations.pop()}'
        )


def check_not_antimeridian(granule_metadata):
    for granule in granule_metadata:
        bbox = granule['polygon'].bounds
        if abs(bbox[0] - bbox[2]) > 180.0 and bbox[0] * bbox[2] < 0.0:
            msg = (
                f'Granule {granule["name"]} crosses the antimeridian.'
                ' Processing across the antimeridian is not currently supported.'
            )
            raise GranuleValidationError(msg)


def format_points(point_string):
    converted_to_float = [float(x) for x in point_string.split(' ')]
    points = [list(t) for t in zip(converted_to_float[1::2], converted_to_float[::2])]
    return points


def get_multipolygon_from_geojson(input_file):
    dem_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), input_file)
    with open(dem_file) as f:
        shp = json.load(f)['features'][0]['geometry']
    polygons = [x.buffer(0) for x in shape(shp).buffer(0).geoms]
    return MultiPolygon(polygons)


def validate_jobs(jobs):
    granules = get_granules(jobs)
    granule_metadata = get_cmr_metadata(granules)

    check_granules_exist(granules, granule_metadata)
    for job in jobs:
        for validator_name in JOB_VALIDATION_MAP[job['job_type']]:
            job_granule_metadata = [granule for granule in granule_metadata if granule['name'] in get_granules([job])]
            module = sys.modules[__name__]
            validator = getattr(module, validator_name)
            validator(job_granule_metadata)
