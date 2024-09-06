AUTORIFT_S2_MEMORY = '7875'
AUTORIFT_LANDSAT_MEMORY = '15750'
RTC_GAMMA_10M_MEMORY = '63200'
WATER_MAP_10M_MEMORY = '126000'


def get_resource_requirements(memory: str) -> dict:
    return {
        'ResourceRequirements': [
            {
                'Type': 'MEMORY',
                'Value': memory,
            }
        ]
    }


def get_insar_isce_burst_memory(job_parameters: dict) -> str:
    # TODO:
    # - update max bursts in job spec and/or add validator to allow diff # of bursts depending on looks?
    # - refine based on more data
    # - refactor lookup structure and/or pull out constants?
    bursts = len(job_parameters['reference'])
    looks = job_parameters['looks']
    if looks == '5x1':
        if bursts < 2:
            return '7500'
        if bursts < 5:
            return '15500'
        if bursts < 13:
            return '31500'
        if bursts < 26:
            return '63500'
    if looks == '10x2':
        if bursts < 10:
            return '7500'
        if bursts < 23:
            return '15500'
        if bursts < 31:
            return '31500'
    if looks == '20x4':
        return '7500'
    raise ValueError(f'No memory value for {bursts} bursts and {looks} looks')


def lambda_handler(event: dict, _) -> dict:
    job_type, job_parameters = event['job_type'], event['job_parameters']

    if job_type == 'INSAR_ISCE_BURST':
        return get_resource_requirements(get_insar_isce_burst_memory(job_parameters))

    if job_type == 'AUTORIFT' and job_parameters['granules'].startswith('S2'):
        return get_resource_requirements(AUTORIFT_S2_MEMORY)

    if job_type == 'AUTORIFT' and job_parameters['granules'].startswith('L'):
        return get_resource_requirements(AUTORIFT_LANDSAT_MEMORY)

    if job_type == 'RTC_GAMMA' and job_parameters['resolution'] in ['10', '20']:
        return get_resource_requirements(RTC_GAMMA_10M_MEMORY)

    if job_type in ['WATER_MAP', 'WATER_MAP_EQ'] and job_parameters['resolution'] in ['10', '20']:
        return get_resource_requirements(WATER_MAP_10M_MEMORY)

    return {}
