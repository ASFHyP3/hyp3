import json
import sys
from collections.abc import Iterable
from pathlib import Path

import requests
import yaml
from shapely.geometry import MultiPolygon, Polygon, shape

from hyp3_api import CMR_URL, multi_burst_validation
from hyp3_api.util import get_granules


DEM_COVERAGE = None


class GranuleValidationError(Exception):
    pass


class BoundsValidationError(Exception):
    pass


with (Path(__file__).parent / 'job_validation_map.yml').open() as job_validation_map_file:
    JOB_VALIDATION_MAP = yaml.safe_load(job_validation_map_file.read())


def _has_sufficient_coverage(granule: Polygon) -> bool:
    global DEM_COVERAGE
    if DEM_COVERAGE is None:
        DEM_COVERAGE = _get_multipolygon_from_geojson('dem_coverage_map_cop30.geojson')

    return granule.intersects(DEM_COVERAGE)


def _get_cmr_metadata(granules: Iterable[str]) -> list[dict]:
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
    return [
        {
            'name': entry.get('producer_granule_id', entry.get('title')),
            'polygon': Polygon(_format_points(entry['polygons'][0][0])),
        }
        for entry in response.json()['feed']['entry']
    ]


def _is_third_party_granule(granule: str) -> bool:
    return granule.startswith('S2') or granule.startswith('L')


def _make_sure_granules_exist(granules: Iterable[str], granule_metadata: list[dict]) -> None:
    found_granules = [granule['name'] for granule in granule_metadata]
    not_found_granules = set(granules) - set(found_granules)
    not_found_granules = {granule for granule in not_found_granules if not _is_third_party_granule(granule)}
    if not_found_granules:
        raise GranuleValidationError(f'Some requested scenes could not be found: {", ".join(not_found_granules)}')


def check_dem_coverage(_, granule_metadata: list[dict]) -> None:
    bad_granules = [g['name'] for g in granule_metadata if not _has_sufficient_coverage(g['polygon'])]
    if bad_granules:
        raise GranuleValidationError(f'Some requested scenes do not have DEM coverage: {", ".join(bad_granules)}')


def check_multi_burst_pairs(job: dict, _) -> None:
    job_parameters = job['job_parameters']
    multi_burst_validation.validate_bursts(job_parameters['reference'], job_parameters['secondary'])


def check_single_burst_pair(job: dict, _) -> None:
    granule1, granule2 = job['job_parameters']['granules']

    granule1_id = '_'.join(granule1.split('_')[1:3])
    granule2_id = '_'.join(granule2.split('_')[1:3])

    if granule1_id != granule2_id:
        raise GranuleValidationError(f'Burst IDs do not match for {granule1} and {granule2}.')

    granule1_pol = granule1.split('_')[4]
    granule2_pol = granule2.split('_')[4]

    if granule1_pol != granule2_pol:
        raise GranuleValidationError(
            f'The requested scenes need to have the same polarization, got: {", ".join([granule1_pol, granule2_pol])}'
        )
    if granule1_pol not in ['VV', 'HH']:
        raise GranuleValidationError(f'Only VV and HH polarizations are currently supported, got: {granule1_pol}')


def check_not_antimeridian(_, granule_metadata: list[dict]) -> None:
    for granule in granule_metadata:
        bbox = granule['polygon'].bounds
        if abs(bbox[0] - bbox[2]) > 180.0 and bbox[0] * bbox[2] < 0.0:
            msg = (
                f'Granule {granule["name"]} crosses the antimeridian.'
                ' Processing across the antimeridian is not currently supported.'
            )
            raise GranuleValidationError(msg)


def _format_points(point_string: str) -> list:
    converted_to_float = [float(x) for x in point_string.split(' ')]
    points = [list(t) for t in zip(converted_to_float[1::2], converted_to_float[::2])]
    return points


def _get_multipolygon_from_geojson(input_file: str) -> MultiPolygon:
    dem_file = Path(__file__).parent / input_file
    with Path(dem_file).open() as f:
        shp = json.load(f)['features'][0]['geometry']
    polygons = [x.buffer(0) for x in shape(shp).buffer(0).geoms]  # type: ignore[attr-defined]
    return MultiPolygon(polygons)


def check_bounds_formatting(job: dict, _) -> None:
    bounds = job['job_parameters']['bounds']
    if bounds == [0.0, 0.0, 0.0, 0.0]:
        raise BoundsValidationError('Invalid bounds. Bounds cannot be [0, 0, 0, 0].')

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


def check_granules_intersecting_bounds(job: dict, granule_metadata: list[dict]) -> None:
    bounds = job['job_parameters']['bounds']
    if bounds == [0.0, 0.0, 0.0, 0.0]:
        raise BoundsValidationError('Invalid bounds. Bounds cannot be [0, 0, 0, 0].')

    bounds = Polygon.from_bounds(*bounds)
    bad_granules = []
    for granule in granule_metadata:
        bbox = granule['polygon']
        if not bbox.intersection(bounds):
            bad_granules.append(granule['name'])
    if bad_granules:
        raise GranuleValidationError(f'The following granules do not intersect the provided bounds: {bad_granules}.')


def check_same_relative_orbits(_, granule_metadata: list[dict]) -> None:
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


def check_bounding_box_size(job: dict, _, max_bounds_area: float = 4.5) -> None:
    bounds = job['job_parameters']['bounds']

    bounds_area = (bounds[3] - bounds[1]) * (bounds[2] - bounds[0])

    if bounds_area > max_bounds_area:
        raise BoundsValidationError(
            f'Bounds must be smaller than {max_bounds_area} degrees squared. Box provided was {bounds_area:.2f}'
        )


def validate_jobs(jobs: list[dict]) -> None:
    granules = get_granules(jobs)
    granule_metadata = _get_cmr_metadata(granules)
    _make_sure_granules_exist(granules, granule_metadata)
    for job in jobs:
        for validator_name in JOB_VALIDATION_MAP[job['job_type']]:
            job_granule_metadata = [granule for granule in granule_metadata if granule['name'] in get_granules([job])]
            module = sys.modules[__name__]
            validator = getattr(module, validator_name)
            validator(job, job_granule_metadata)
