from set_container_overrides import (
    AUTORIFT_LANDSAT_MEMORY,
    AUTORIFT_S2_MEMORY,
    RTC_GAMMA_10M_MEMORY,
    WATER_MAP_10M_MEMORY,
    lambda_handler,
)


def test_set_container_overrides_default():
    assert lambda_handler(
        {
            'job_type': 'foo',
            'job_parameters': {},
        },
        None,
    ) == {}


def test_set_container_overrides_autorift_s2():
    assert lambda_handler(
        {
            'job_type': 'AUTORIFT',
            'job_parameters': {'granules': 'S2B_'},
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


def test_set_container_overrides_autorift_landsat():
    assert lambda_handler(
        {
            'job_type': 'AUTORIFT',
            'job_parameters': {'granules': 'LC08_'},
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


def test_set_container_overrides_rtc_gamma_10m():
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


def test_set_container_overrides_water_map_10m():
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
