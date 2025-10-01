import json
import os
import sys
from collections.abc import Iterable
from datetime import date, datetime
from pathlib import Path

import requests
import yaml
from shapely.geometry import MultiPolygon, Polygon, box, shape

from hyp3_api import CMR_URL, multi_burst_validation
from hyp3_api.util import get_granules


DEM_COVERAGE = None


class InternalValidationError(Exception):
    """Raised for internal validation errors that should not be displayed to the user."""

    pass


class ValidationError(Exception):
    pass


class CmrError(Exception):
    """Raised when the CMR query has failed and is required for the current job type."""

    pass


with (Path(__file__).parent / 'job_validation_map.yml').open() as job_validation_map_file:
    JOB_VALIDATION_MAP = yaml.safe_load(job_validation_map_file.read())


def _has_sufficient_coverage(granule: Polygon) -> bool:
    global DEM_COVERAGE
    if DEM_COVERAGE is None:
        DEM_COVERAGE = _get_multipolygon_from_geojson('dem_coverage_map_cop30.geojson')

    return granule.intersects(DEM_COVERAGE)


def _get_cmr_metadata(granules: Iterable[str]) -> list[dict]:
    if not granules:
        return []

    cmr_parameters = {
        'granule_ur': [f'{granule}*' for granule in granules],
        'options[granule_ur][pattern]': 'true',
        'provider': 'ASF',
        'short_name': [
            'SENTINEL-1A_SLC',
            'SENTINEL-1B_SLC',
            'SENTINEL-1C_SLC',
            'SENTINEL-1A_SP_GRD_HIGH',
            'SENTINEL-1B_SP_GRD_HIGH',
            'SENTINEL-1C_SP_GRD_HIGH',
            'SENTINEL-1A_DP_GRD_HIGH',
            'SENTINEL-1B_DP_GRD_HIGH',
            'SENTINEL-1C_DP_GRD_HIGH',
            'SENTINEL-1_BURSTS',
            'SENTINEL-1A_RAW',
            'SENTINEL-1B_RAW',
            'SENTINEL-1C_RAW',
        ],
        'page_size': 2000,
    }
    response = requests.post(CMR_URL, data=cmr_parameters)

    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        print(f'CMR search failed: {e}')
        return []

    granule_metadata = [
        {
            'name': entry.get('producer_granule_id', entry.get('title')),
            'polygon': Polygon(_format_points(entry['polygons'][0][0])),
        }
        for entry in response.json()['feed']['entry']
    ]

    _make_sure_granules_exist(granules, granule_metadata)

    return granule_metadata


def _is_third_party_granule(granule: str) -> bool:
    return granule.startswith('S2') or granule.startswith('L')


def _make_sure_granules_exist(granules: Iterable[str], granule_metadata: list[dict]) -> None:
    found_granules = [granule['name'] for granule in granule_metadata]
    not_found_granules = set(granules) - set(found_granules)
    not_found_granules = {granule for granule in not_found_granules if not _is_third_party_granule(granule)}
    if not_found_granules:
        raise ValidationError(f'Some requested scenes could not be found: {", ".join(not_found_granules)}')


def check_cmr_query_succeeded(job: dict, granule_metadata: list[dict]) -> None:
    if not granule_metadata:
        raise CmrError(
            f'Cannot validate job(s) of type {job["job_type"]} because CMR query failed. Please try again later.'
        )


def check_dem_coverage(_, granule_metadata: list[dict]) -> None:
    bad_granules = [g['name'] for g in granule_metadata if not _has_sufficient_coverage(g['polygon'])]
    if bad_granules:
        raise ValidationError(f'Some requested scenes do not have DEM coverage: {", ".join(bad_granules)}')


def check_multi_burst_pairs(job: dict, _) -> None:
    job_parameters = job['job_parameters']
    multi_burst_validation.validate_bursts(job_parameters['reference'], job_parameters['secondary'])


def check_multi_burst_max_length(job: dict, _, max_pairs: int = 15) -> None:
    job_parameters = job['job_parameters']
    reference, secondary = job_parameters['reference'], job_parameters['secondary']
    if len(reference) > max_pairs or len(secondary) > max_pairs:
        raise multi_burst_validation.MultiBurstValidationError(
            f'Must provide no more than {max_pairs} scene pairs, got {len(reference)} reference and {len(secondary)} secondary'
        )


def check_single_burst_pair(job: dict, _) -> None:
    granule1, granule2 = job['job_parameters']['granules']

    granule1_id = '_'.join(granule1.split('_')[1:3])
    granule2_id = '_'.join(granule2.split('_')[1:3])

    if granule1_id != granule2_id:
        raise ValidationError(f'Burst IDs do not match for {granule1} and {granule2}.')

    granule1_pol = granule1.split('_')[4]
    granule2_pol = granule2.split('_')[4]

    if granule1_pol != granule2_pol:
        raise ValidationError(
            f'The requested scenes need to have the same polarization, got: {", ".join([granule1_pol, granule2_pol])}'
        )
    if granule1_pol not in ['VV', 'HH']:
        raise ValidationError(f'Only VV and HH polarizations are currently supported, got: {granule1_pol}')


def check_not_antimeridian(_, granule_metadata: list[dict]) -> None:
    for granule in granule_metadata:
        bbox = granule['polygon'].bounds
        if abs(bbox[0] - bbox[2]) > 180.0 and bbox[0] * bbox[2] < 0.0:
            msg = (
                f'Granule {granule["name"]} crosses the antimeridian.'
                ' Processing across the antimeridian is not currently supported.'
            )
            raise ValidationError(msg)


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
        raise ValidationError('Invalid bounds. Bounds cannot be [0, 0, 0, 0].')

    if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        raise ValidationError(
            'Invalid order for bounds. Bounds should be ordered [min lon, min lat, max lon, max lat].'
        )

    def bad_lat(lat: float) -> bool:
        return lat > 90 or lat < -90

    def bad_lon(lon: float) -> bool:
        return lon > 180 or lon < -180

    if any([bad_lon(bounds[0]), bad_lon(bounds[2]), bad_lat(bounds[1]), bad_lat(bounds[3])]):
        raise ValidationError(
            'Invalid lon/lat value(s) in bounds. Bounds should be ordered [min lon, min lat, max lon, max lat].'
        )


def check_granules_intersecting_bounds(job: dict, granule_metadata: list[dict]) -> None:
    bounds = job['job_parameters']['bounds']
    if bounds == [0.0, 0.0, 0.0, 0.0]:
        raise ValidationError('Invalid bounds. Bounds cannot be [0, 0, 0, 0].')

    bounds = Polygon.from_bounds(*bounds)
    bad_granules = []
    for granule in granule_metadata:
        bbox = granule['polygon']
        if not bbox.intersection(bounds):
            bad_granules.append(granule['name'])
    if bad_granules:
        raise ValidationError(f'The following granules do not intersect the provided bounds: {bad_granules}.')


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
            raise ValidationError(
                f'Relative orbit number for {granule["name"]} does not match that of the previous granules: '
                f'{relative_orbit} is not {previous_relative_orbit}.'
            )


def check_bounding_box_size(job: dict, _, max_bounds_area: float = 4.5) -> None:
    bounds = job['job_parameters']['bounds']

    bounds_area = (bounds[3] - bounds[1]) * (bounds[2] - bounds[0])

    if bounds_area > max_bounds_area:
        raise ValidationError(
            f'Bounds must be smaller than {max_bounds_area} degrees squared. Box provided was {bounds_area:.2f}'
        )


def check_opera_rtc_s1_bounds(_, granule_metadata: list[dict]) -> None:
    opera_rtc_s1_bounds = box(-180, -60, 180, 90)
    for granule in granule_metadata:
        if not granule['polygon'].intersects(opera_rtc_s1_bounds):
            raise ValidationError(
                f'Granule {granule["name"]} is south of -60 degrees latitude and outside the valid processing extent '
                f'for OPERA RTC-S1 products.'
            )


def check_aria_s1_gunw_dates(job: dict, _) -> None:
    def format_date(key: str) -> date:
        return date.fromisoformat(job['job_parameters'][key])

    reference, secondary = format_date('reference_date'), format_date('secondary_date')
    _validate_date_during_s1('reference_date', reference)
    _validate_date_during_s1('secondary_date', secondary)

    if secondary >= reference:
        raise ValidationError('secondary date must be earlier than reference date.')


def _validate_date_during_s1(date_name: str, date_value: date) -> None:
    s1_start_date = date(2014, 6, 15)
    todays_date = date.today()

    if date_value > todays_date:
        raise ValidationError(f'"{date_name}" is {date_value} which is a date in the future.')

    if date_value < s1_start_date:
        raise ValidationError(
            f'"{date_name}" is {date_value} which is before the start of the sentinel 1 mission ({s1_start_date}).'
        )


def check_opera_rtc_s1_date(job: dict, _) -> None:
    granules = job['job_parameters']['granules']
    if len(granules) != 1:
        raise InternalValidationError(f'Expected 1 granule, got {granules}')

    granule = granules[0]
    granule_date = datetime.strptime(granule.split('_')[3][:8], '%Y%m%d').date()

    # Disallow IPF version < 002.70 according to the dates given at https://sar-mpc.eu/processor/ipf/
    # Also see https://github.com/ASFHyP3/hyp3/issues/2739
    if granule_date < date(2016, 4, 14):
        raise ValidationError(
            f'Granule {granule} was acquired before 2016-04-14 '
            'and is not available for On-Demand OPERA RTC-S1 processing.'
        )

    end_date_str = os.environ['OPERA_RTC_S1_END_DATE']
    if end_date_str == 'Default':
        end_date_str = '2022-01-01'

    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    if granule_date >= end_date:
        raise ValidationError(
            f'Granule {granule} was acquired on or after {end_date_str} '
            'and is not available for On-Demand OPERA RTC-S1 processing. '
            'You can download the product from the ASF DAAC archive.'
        )


def validate_jobs(jobs: list[dict]) -> None:
    granules = get_granules(jobs)
    granule_metadata = _get_cmr_metadata(granules)

    for job in jobs:
        for validator_name in JOB_VALIDATION_MAP[job['job_type']]:
            job_granule_metadata = [granule for granule in granule_metadata if granule['name'] in get_granules([job])]
            module = sys.modules[__name__]
            validator = getattr(module, validator_name)
            validator(job, job_granule_metadata)
