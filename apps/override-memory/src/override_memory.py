AUTORIFT_S2_MEMORY = 7875
AUTORIFT_LANDSAT_MEMORY = 15750
RTC_GAMMA_10M_MEMORY = 63200
WATER_MAP_10M_MEMORY = 126000


def get_resource_requirements(memory: int) -> dict:
    return {
        'ResourceRequirements': [
            {
                'Type': 'MEMORY',
                'Value': memory,
            }
        ]
    }


def lambda_handler(event: dict, _) -> dict:
    job_type, job_parameters = event['job_type'], event['job_parameters']

    if job_type == 'AUTORIFT' and job_parameters['granules'][0].startswith('S2'):
        return get_resource_requirements(AUTORIFT_S2_MEMORY)

    if job_type == 'AUTORIFT' and job_parameters['granules'][0].startswith('L'):
        return get_resource_requirements(AUTORIFT_LANDSAT_MEMORY)

    if job_type == 'RTC_GAMMA' and job_parameters['resolution'] in ['10', '20']:
        return get_resource_requirements(RTC_GAMMA_10M_MEMORY)

    if job_type in ['WATER_MAP', 'WATER_MAP_EQ'] and job_parameters['resolution'] in ['10', '20']:
        return get_resource_requirements(WATER_MAP_10M_MEMORY)

    return {}
