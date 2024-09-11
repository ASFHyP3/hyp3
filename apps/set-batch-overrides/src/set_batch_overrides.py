AUTORIFT_S2_MEMORY = '7875'
AUTORIFT_LANDSAT_MEMORY = '15750'
RTC_GAMMA_10M_MEMORY = '63200'
WATER_MAP_10M_MEMORY = '126000'
INSAR_ISCE_BURST_MEMORY_8G = '7500'
INSAR_ISCE_BURST_MEMORY_16G = '15500'
INSAR_ISCE_BURST_MEMORY_32G = '31500'
INSAR_ISCE_BURST_MEMORY_64G = '63500'
INSAR_ISCE_BURST_MEMORY_128G = '127500'


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
    bursts = len(job_parameters['reference'].split(' '))
    looks = job_parameters['looks']
    if looks == '5x1':
        if bursts < 2:
            return INSAR_ISCE_BURST_MEMORY_8G
        if bursts < 4:
            return INSAR_ISCE_BURST_MEMORY_16G
        if bursts < 11:
            return INSAR_ISCE_BURST_MEMORY_32G
        if bursts < 25:
            return INSAR_ISCE_BURST_MEMORY_64G
        if bursts < 31:
            return INSAR_ISCE_BURST_MEMORY_128G
    if looks == '10x2':
        if bursts < 10:
            return INSAR_ISCE_BURST_MEMORY_8G
        if bursts < 21:
            return INSAR_ISCE_BURST_MEMORY_16G
        if bursts < 31:
            return INSAR_ISCE_BURST_MEMORY_32G
    if looks == '20x4':
        if bursts < 23:
            return INSAR_ISCE_BURST_MEMORY_8G
        if bursts < 31:
            return INSAR_ISCE_BURST_MEMORY_16G
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
