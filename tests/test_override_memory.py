from override_memory import (
    AUTORIFT_LANDSAT_MEMORY,
    AUTORIFT_S2_MEMORY,
    RTC_GAMMA_10M_MEMORY,
    WATER_MAP_10M_MEMORY,
    lambda_handler,
)


def test_override_memory_default():
    assert lambda_handler(
        {
            'job_type': 'foo',
            'job_parameters': {},
        },
        None,
    ) == {}


def test_override_memory_autorift_s2():
    assert lambda_handler(
        {
            'job_type': 'AUTORIFT',
            'job_parameters': {'granules': ['S2B_MSIL1C_20200105T152259_N0208_R039_T13CES_20200105T181230']},
        },
        None,
    ) == {
        'ResourceRequirements': [
            {
                'Type': 'MEMORY',
                'Value': AUTORIFT_S2_MEMORY,
            }
        ]
    }


def test_override_memory_autorift_landsat():
    assert lambda_handler(
        {
            'job_type': 'AUTORIFT',
            'job_parameters': {'granules': ['LC08_L1GT_118112_20210107_20210107_02_T2']},
        },
        None,
    ) == {
        'ResourceRequirements': [
            {
                'Type': 'MEMORY',
                'Value': AUTORIFT_LANDSAT_MEMORY,
            }
        ]
    }


def test_override_memory_rtc_gamma_10m():
    assert lambda_handler(
        {
            'job_type': 'RTC_GAMMA',
            'job_parameters': {'resolution': '10'},
        },
        None,
    ) == {
        'ResourceRequirements': [
            {
                'Type': 'MEMORY',
                'Value': RTC_GAMMA_10M_MEMORY,
            }
        ]
    }
    assert lambda_handler(
        {
            'job_type': 'RTC_GAMMA',
            'job_parameters': {'resolution': '20'},
        },
        None,
    ) == {
        'ResourceRequirements': [
            {
                'Type': 'MEMORY',
                'Value': RTC_GAMMA_10M_MEMORY,
            }
        ]
    }


def test_override_memory_water_map_10m():
    assert lambda_handler(
        {
            'job_type': 'WATER_MAP',
            'job_parameters': {'resolution': '10'},
        },
        None,
    ) == {
        'ResourceRequirements': [
            {
                'Type': 'MEMORY',
                'Value': WATER_MAP_10M_MEMORY,
            }
        ]
    }
    assert lambda_handler(
        {
            'job_type': 'WATER_MAP',
            'job_parameters': {'resolution': '20'},
        },
        None,
    ) == {
        'ResourceRequirements': [
            {
                'Type': 'MEMORY',
                'Value': WATER_MAP_10M_MEMORY,
            }
        ]
    }
    assert lambda_handler(
        {
            'job_type': 'WATER_MAP_EQ',
            'job_parameters': {'resolution': '10'},
        },
        None,
    ) == {
        'ResourceRequirements': [
            {
                'Type': 'MEMORY',
                'Value': WATER_MAP_10M_MEMORY,
            }
        ]
    }
    assert lambda_handler(
        {
            'job_type': 'WATER_MAP_EQ',
            'job_parameters': {'resolution': '20'},
        },
        None,
    ) == {
        'ResourceRequirements': [
            {
                'Type': 'MEMORY',
                'Value': WATER_MAP_10M_MEMORY,
            }
        ]
    }
