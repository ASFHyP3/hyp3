from math import ceil


AUTORIFT_S2_MEMORY = '7875'
AUTORIFT_LANDSAT_MEMORY = '15750'
AUTORIFT_S1_MEMORY = '31500'

RTC_GAMMA_10M_MEMORY = '63200'
WATER_MAP_10M_MEMORY = '126000'

INSAR_ISCE_BURST_MEMORY_8G = '7500'
INSAR_ISCE_BURST_MEMORY_16G = '15500'
INSAR_ISCE_BURST_MEMORY_32G = '31500'
INSAR_ISCE_BURST_MEMORY_64G = '63500'
INSAR_ISCE_BURST_MEMORY_128G = '127500'


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


def get_autorift_memory(job_parameters: dict) -> str:
    granules = job_parameters.get('granules', []) + job_parameters.get('reference', [])
    granules = [granule for granule in granules if granule]

    if granules[0].startswith('S2'):
        return AUTORIFT_S2_MEMORY
    elif granules[0].startswith('L'):
        return AUTORIFT_LANDSAT_MEMORY

    return AUTORIFT_S1_MEMORY


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


def get_vcpus_from_memory(memory: str, mibs_per_vcpu: int = 8000) -> str:
    """Determine available vCPUs (threads) from memory reservation

    Args:
        memory: Memory reservation for job in MiBs
        mibs_per_vcpu: Number of MiBs per VCPU. Typically, 8000 for the R instance family, 4000 for M, and 20000 for C.

    Returns:
        vcpus: Number of available vCPUs
    """
    return str(ceil(int(memory) / mibs_per_vcpu))


def lambda_handler(event: dict, _) -> dict:
    job_type, job_parameters = event['job_type'], event['job_parameters']

    if job_type == 'INSAR_ISCE_MULTI_BURST':
        burst_memory = get_insar_isce_burst_memory(job_parameters)
        omp_num_threads = get_vcpus_from_memory(burst_memory)
        return get_container_overrides(burst_memory, omp_num_threads)

    if job_type == 'AUTORIFT':
        autorift_memory = get_autorift_memory(job_parameters)
        omp_num_threads = get_vcpus_from_memory(autorift_memory)
        return get_container_overrides(autorift_memory, omp_num_threads)

    if job_type == 'RTC_GAMMA' and job_parameters['resolution'] in [10, 20]:
        return get_container_overrides(RTC_GAMMA_10M_MEMORY)

    if job_type in ['WATER_MAP', 'WATER_MAP_EQ'] and job_parameters['resolution'] in [10, 20]:
        return get_container_overrides(WATER_MAP_10M_MEMORY)

    return {}
