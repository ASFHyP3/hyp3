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
        return get_resource_requirements(7875)

    if job_type == 'AUTORIFT' and job_parameters['granules'][0].startswith('L'):
        return get_resource_requirements(15750)

    if job_type == 'RTC_GAMMA' and job_parameters['resolution'] in ['10', '20']:
        return get_resource_requirements(63200)

    if job_type in ['WATER_MAP', 'WATER_MAP_EQ'] and job_parameters['resolution'] in ['10', '20']:
        return get_resource_requirements(126000)

    return {}
