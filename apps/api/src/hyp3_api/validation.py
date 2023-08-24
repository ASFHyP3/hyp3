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
DEM_COVERAGE_LEGACY = None


class GranuleValidationError(Exception):
    pass


with open(Path(__file__).parent / 'job_validation_map.yml') as f:
    JOB_VALIDATION_MAP = yaml.safe_load(f.read())


def has_sufficient_coverage(granule: Polygon, buffer: float = 0.15, threshold: float = 0.2, legacy=False):
    if legacy:
        global DEM_COVERAGE_LEGACY
        if DEM_COVERAGE_LEGACY is None:
            DEM_COVERAGE_LEGACY = get_multipolygon_from_geojson('dem_coverage_map_legacy.geojson')

        buffered_granule = granule.buffer(buffer)
        covered_area = buffered_granule.intersection(DEM_COVERAGE_LEGACY).area

        return covered_area / buffered_granule.area >= threshold
    else:
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


def check_dem_coverage(job, granule_metadata):
    legacy = job['job_parameters'].get('dem_name') == 'legacy'
    bad_granules = [g['name'] for g in granule_metadata if not has_sufficient_coverage(g['polygon'], legacy=legacy)]
    if bad_granules:
        raise GranuleValidationError(f'Some requested scenes do not have DEM coverage: {", ".join(bad_granules)}')


def check_same_burst_ids(job, granule_metadata):
    burst_ids = [g['name'].split('_')[1] for g in granule_metadata]
    ref_burst_id = burst_ids[0]
    sec_burst_id = burst_ids[1]
    if ref_burst_id != sec_burst_id:
        raise GranuleValidationError(f'The requested scenes do not have the same burst id: {ref_burst_id} and {sec_burst_id}')


def check_valid_polarizations(job, granule_metadata):
    polarizations = [g['name'].split('_')[4] for g in granule_metadata]
    ref_polarization = polarizations[0]
    sec_polarization = polarizations[1]
    if ref_polarization != sec_polarization:
        raise GranuleValidationError(f'The requested scenes do not have the same polarization: {ref_polarization} and {sec_polarization}')
    if ref_polarization != 'VV' and ref_polarization != 'HH':
        raise GranuleValidationError(f'Only VV and HH polarizations are currently supported, got: {ref_polarization}')


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
            validator(job, job_granule_metadata)