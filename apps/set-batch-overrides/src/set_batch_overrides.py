AUTORIFT_S2_MEMORY = '7875'
AUTORIFT_LANDSAT_MEMORY = '15750'
RTC_GAMMA_10M_MEMORY = '63200'
WATER_MAP_10M_MEMORY = '126000'

INSAR_ISCE_BURST_MEMORY_8G = '7500'
INSAR_ISCE_BURST_MEMORY_16G = '15500'
INSAR_ISCE_BURST_MEMORY_32G = '31500'
INSAR_ISCE_BURST_MEMORY_64G = '63500'
INSAR_ISCE_BURST_MEMORY_128G = '127500'

# vCPU = Memory/8 for r6 instance types
INSAR_ISCE_BURST_OMP_NUM_THREADS = {
    INSAR_ISCE_BURST_MEMORY_8G: '1',
    INSAR_ISCE_BURST_MEMORY_16G: '2',
    INSAR_ISCE_BURST_MEMORY_32G: '4',
    INSAR_ISCE_BURST_MEMORY_64G: '8',
    INSAR_ISCE_BURST_MEMORY_128G: '16',
}


def get_container_overrides(memory: str, omp_num_threads: str | None = None) -> dict:
    container_overrides = {
        'ResourceRequirements': [
            {
                'Type': 'MEMORY',
                'Value': memory,
            }
        ]
    }
    if omp_num_threads is not None:
        container_overrides['Environment'] = [{'Name': 'OMP_NUM_THREADS', 'Value': omp_num_threads}]
    return container_overrides


def get_insar_isce_burst_memory(job_parameters: dict) -> str:
    looks = job_parameters['looks']
    bursts = len(job_parameters['reference'])
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
        if bursts < 8:
            return INSAR_ISCE_BURST_MEMORY_8G
        if bursts < 21:
            return INSAR_ISCE_BURST_MEMORY_16G
        if bursts < 31:
            return INSAR_ISCE_BURST_MEMORY_32G
    if looks == '20x4':
        if bursts < 16:
            return INSAR_ISCE_BURST_MEMORY_8G
        if bursts < 31:
            return INSAR_ISCE_BURST_MEMORY_16G
    raise ValueError(f'No memory value for {bursts} bursts and {looks} looks')


def lambda_handler(event: dict, _) -> dict:
    job_type, job_parameters = event['job_type'], event['job_parameters']

    if job_type == 'INSAR_ISCE_BURST':
        memory = get_insar_isce_burst_memory(job_parameters)
        omp_num_threads = INSAR_ISCE_BURST_OMP_NUM_THREADS[memory]
        return get_container_overrides(memory, omp_num_threads)

    if job_type == 'AUTORIFT' and job_parameters['granules'][0].startswith('S2'):
        return get_container_overrides(AUTORIFT_S2_MEMORY)

    if job_type == 'AUTORIFT' and job_parameters['granules'][0].startswith('L'):
        return get_container_overrides(AUTORIFT_LANDSAT_MEMORY)

    if job_type == 'RTC_GAMMA' and job_parameters['resolution'] in [10, 20]:
        return get_container_overrides(RTC_GAMMA_10M_MEMORY)

    if job_type in ['WATER_MAP', 'WATER_MAP_EQ'] and job_parameters['resolution'] in [10, 20]:
        return get_container_overrides(WATER_MAP_10M_MEMORY)

    return {}
