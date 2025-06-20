from datetime import datetime, timedelta


class MultiBurstValidationError(Exception):
    pass


def _num_swath_pol(scene: str) -> str:
    parts = scene.split('_')
    num = parts[1]
    swath = parts[2]
    pol = parts[4]
    return '_'.join([num, swath, pol])


def _burst_datetime(scene: str) -> datetime:
    datetime_str = scene.split('_')[3]
    return datetime.strptime(datetime_str, '%Y%m%dT%H%M%S')


def validate_bursts(reference: list[str], secondary: list[str]) -> None:
    """Check whether the reference and secondary bursts are valid.

    Args:
        reference: Reference granule(s)
        secondary: Secondary granule(s)
    """
    # **WARNING:** Changes to this function must be kept in sync with the hyp3-isce2 function
    # until https://github.com/ASFHyP3/hyp3-lib/issues/340 is done

    if len(reference) < 1 or len(secondary) < 1:
        raise MultiBurstValidationError('Must include at least 1 reference scene and 1 secondary scene')

    if len(reference) != len(secondary):
        raise MultiBurstValidationError(
            f'Must provide the same number of reference and secondary scenes, got {len(reference)} reference and {len(secondary)} secondary'
        )

    ref_num_swath_pol = {_num_swath_pol(ref) for ref in reference}
    sec_num_swath_pol = {_num_swath_pol(sec) for sec in secondary}
    if ref_num_swath_pol != sec_num_swath_pol:
        raise MultiBurstValidationError(
            'Burst number + swath + polarization identifiers must be the same for reference scenes and secondary scenes'
        )

    if len(ref_num_swath_pol) != len(reference):
        raise MultiBurstValidationError('Each reference scene must have a unique burst number + swath + polarization identifier')

    pols = list(set(g.split('_')[4] for g in reference))

    if len(pols) > 1:
        raise MultiBurstValidationError(
            f'Scenes must have the same polarization. Polarizations present: {", ".join(sorted(pols))}'
        )

    if pols[0] not in ['VV', 'HH']:
        raise MultiBurstValidationError(f'{pols[0]} polarization is not currently supported, only VV and HH')

    ref_datetimes = sorted(_burst_datetime(g) for g in reference)
    sec_datetimes = sorted(_burst_datetime(g) for g in secondary)

    if ref_datetimes[-1] - ref_datetimes[0] > timedelta(minutes=2):
        raise MultiBurstValidationError(
            'Reference scenes must fall within a 2-minute window in order to ensure they were collected during the same pass'
        )

    if sec_datetimes[-1] - sec_datetimes[0] > timedelta(minutes=2):
        raise MultiBurstValidationError(
            'Secondary scenes must fall within a 2-minute window in order to ensure they were collected during the same pass'
        )

    if ref_datetimes[-1] >= sec_datetimes[0]:
        raise MultiBurstValidationError('Reference scenes must be older than secondary scenes')
