import json
import os
import sys
from copy import deepcopy
from pathlib import Path

import requests
import yaml
from shapely.geometry import MultiPolygon, Polygon, shape

from hyp3_api import CMR_URL
from hyp3_api.util import get_granules

DEM_COVERAGE = None


class GranuleValidationError(Exception):
    pass


class BoundsValidationError(Exception):
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
            'polygon': Polygon(format_points(entry['polygons'][0][0])),
        }
        for entry in response.json()['feed']['entry']
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


def check_dem_coverage(_, granule_metadata):
    bad_granules = [g['name'] for g in granule_metadata if not has_sufficient_coverage(g['polygon'])]
    if bad_granules:
        raise GranuleValidationError(f'Some requested scenes do not have DEM coverage: {", ".join(bad_granules)}')


def check_same_burst_ids(job, _):
    refs = job['job_parameters']['reference']
    secs = job['job_parameters']['secondary']
    ref_ids = ['_'.join(ref.split('_')[1:3]) for ref in refs]
    sec_ids = ['_'.join(sec.split('_')[1:3]) for sec in secs]
    if len(ref_ids) != len(sec_ids):
        raise GranuleValidationError(
            f'Number of reference and secondary scenes must match, got: '
            f'{len(ref_ids)} references and {len(sec_ids)} secondaries'
        )
    for i in range(len(ref_ids)):
        if ref_ids[i] != sec_ids[i]:
            raise GranuleValidationError(f'Burst IDs do not match for {refs[i]} and {secs[i]}.')
    if len(set(ref_ids)) != len(ref_ids):
        duplicate_pair_id = next(ref_id for ref_id in ref_ids if ref_ids.count(ref_id) > 1)
        raise GranuleValidationError(
            f'The requested scenes have more than 1 pair with the following burst ID: {duplicate_pair_id}.'
        )


def check_valid_polarizations(job, _):
    polarizations = set(granule.split('_')[4] for granule in get_granules([job]))
    if len(polarizations) > 1:
        raise GranuleValidationError(
            f'The requested scenes need to have the same polarization, got: {", ".join(polarizations)}'
        )
    if not polarizations.issubset({'VV', 'HH'}):
        raise GranuleValidationError(
            f'Only VV and HH polarizations are currently supported, got: {polarizations.pop()}'
        )


def check_not_antimeridian(_, granule_metadata):
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


def check_bounds_formatting(job, _):
    bounds = job['job_parameters']['bounds']
    if bounds == [0.0, 0.0, 0.0, 0.0]:
        return

    if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        raise BoundsValidationError(
            'Invalid order for bounds. Bounds should be ordered [min lon, min lat, max lon, max lat].'
        )

    def bad_lat(lat):
        return lat > 90 or lat < -90

    def bad_lon(lon):
        return lon > 180 or lon < -180

    if any([bad_lon(bounds[0]), bad_lon(bounds[2]), bad_lat(bounds[1]), bad_lat(bounds[3])]):
        raise BoundsValidationError(
            'Invalid lon/lat value(s) in bounds. Bounds should be ordered [min lon, min lat, max lon, max lat].'
        )


def check_granules_intersecting_bounds(job, granule_metadata):
    bounds = job['job_parameters']['bounds']
    if bounds == [0.0, 0.0, 0.0, 0.0]:
        bounds = granule_metadata[0]['polygon']
    else:
        bounds = Polygon.from_bounds(*bounds)
    bad_granules = []
    for granule in granule_metadata:
        bbox = granule['polygon']
        if not bbox.intersection(bounds):
            bad_granules.append(granule['name'])
    if bad_granules:
        raise GranuleValidationError(f'The following granules do not intersect the provided bounds: {bad_granules}.')


def check_same_relative_orbits(job, granule_metadata):
    previous_relative_orbit = None
    for granule in granule_metadata:
        name_split = granule['name'].split('_')
        absolute_orbit = name_split[7]
        # "Relationship between relative and absolute orbit numbers": https://sentiwiki.copernicus.eu/web/s1-products
        offset = 73 if name_split[0] == 'S1A' else 27
        relative_orbit = ((int(absolute_orbit) - offset) % 175) + 1
        if not previous_relative_orbit:
            previous_relative_orbit = relative_orbit
        if relative_orbit != previous_relative_orbit:
            raise GranuleValidationError(
                f'Relative orbit number for {granule["name"]} does not match that of the previous granules: '
                f'{relative_orbit} is not {previous_relative_orbit}.'
            )


def convert_single_burst_jobs(jobs: list[dict]) -> list[dict]:
    jobs = deepcopy(jobs)
    for job in jobs:
        if job['job_type'] == 'INSAR_ISCE_BURST':
            job_parameters = job['job_parameters']
            ref, sec = job_parameters.pop('granules')
            job_parameters['reference'], job_parameters['secondary'] = [ref], [sec]
    return jobs


def validate_jobs(jobs: list[dict]) -> None:
    jobs = convert_single_burst_jobs(jobs)

    granules = get_granules(jobs)
    granule_metadata = get_cmr_metadata(granules)

    check_granules_exist(granules, granule_metadata)
    for job in jobs:
        for validator_name in JOB_VALIDATION_MAP[job['job_type']]:
            job_granule_metadata = [granule for granule in granule_metadata if granule['name'] in get_granules([job])]
            module = sys.modules[__name__]
            validator = getattr(module, validator_name)
            validator(job, job_granule_metadata)
