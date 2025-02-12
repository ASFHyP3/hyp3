import pytest

from set_batch_overrides import (
    AUTORIFT_LANDSAT_MEMORY,
    AUTORIFT_S2_MEMORY,
    INSAR_ISCE_BURST_MEMORY_8G,
    INSAR_ISCE_BURST_MEMORY_16G,
    INSAR_ISCE_BURST_MEMORY_32G,
    INSAR_ISCE_BURST_MEMORY_64G,
    INSAR_ISCE_BURST_MEMORY_128G,
    RTC_GAMMA_10M_MEMORY,
    WATER_MAP_10M_MEMORY,
    lambda_handler,
)


def mock_insar_isce_burst_job(looks: str, bursts: int) -> dict:
    return {
        'job_type': 'INSAR_ISCE_MULTI_BURST',
        'job_parameters': {
            'looks': looks,
            'reference': ['foo' for _ in range(bursts)],
        },
    }


def test_set_batch_overrides_default():
    assert (
        lambda_handler(
            {
                'job_type': 'foo',
                'job_parameters': {},
            },
            None,
        )
        == {}
    )


def test_set_batch_overrides_insar_isce_burst_5x1():
    assert lambda_handler(mock_insar_isce_burst_job('5x1', bursts=1), None) == {
        'ResourceRequirements': [
            {
                'Type': 'MEMORY',
                'Value': INSAR_ISCE_BURST_MEMORY_8G,
            }
        ],
        'Environment': [{'Name': 'OMP_NUM_THREADS', 'Value': '1'}],
    }
    for n in range(2, 4):
        assert lambda_handler(mock_insar_isce_burst_job('5x1', bursts=n), None) == {
            'ResourceRequirements': [
                {
                    'Type': 'MEMORY',
                    'Value': INSAR_ISCE_BURST_MEMORY_16G,
                }
            ],
            'Environment': [{'Name': 'OMP_NUM_THREADS', 'Value': '2'}],
        }
    for n in range(4, 11):
        assert lambda_handler(mock_insar_isce_burst_job('5x1', bursts=n), None) == {
            'ResourceRequirements': [
                {
                    'Type': 'MEMORY',
                    'Value': INSAR_ISCE_BURST_MEMORY_32G,
                }
            ],
            'Environment': [{'Name': 'OMP_NUM_THREADS', 'Value': '4'}],
        }
    for n in range(11, 25):
        assert lambda_handler(mock_insar_isce_burst_job('5x1', bursts=n), None) == {
            'ResourceRequirements': [
                {
                    'Type': 'MEMORY',
                    'Value': INSAR_ISCE_BURST_MEMORY_64G,
                }
            ],
            'Environment': [{'Name': 'OMP_NUM_THREADS', 'Value': '8'}],
        }
    for n in range(25, 31):
        assert lambda_handler(mock_insar_isce_burst_job('5x1', bursts=n), None) == {
            'ResourceRequirements': [
                {
                    'Type': 'MEMORY',
                    'Value': INSAR_ISCE_BURST_MEMORY_128G,
                }
            ],
            'Environment': [{'Name': 'OMP_NUM_THREADS', 'Value': '16'}],
        }


def test_set_batch_overrides_insar_isce_burst_10x2():
    for n in range(1, 8):
        assert lambda_handler(mock_insar_isce_burst_job('10x2', bursts=n), None) == {
            'ResourceRequirements': [
                {
                    'Type': 'MEMORY',
                    'Value': INSAR_ISCE_BURST_MEMORY_8G,
                }
            ],
            'Environment': [{'Name': 'OMP_NUM_THREADS', 'Value': '1'}],
        }
    for n in range(8, 21):
        assert lambda_handler(mock_insar_isce_burst_job('10x2', bursts=n), None) == {
            'ResourceRequirements': [
                {
                    'Type': 'MEMORY',
                    'Value': INSAR_ISCE_BURST_MEMORY_16G,
                }
            ],
            'Environment': [{'Name': 'OMP_NUM_THREADS', 'Value': '2'}],
        }
    for n in range(21, 31):
        assert lambda_handler(mock_insar_isce_burst_job('10x2', bursts=n), None) == {
            'ResourceRequirements': [
                {
                    'Type': 'MEMORY',
                    'Value': INSAR_ISCE_BURST_MEMORY_32G,
                }
            ],
            'Environment': [{'Name': 'OMP_NUM_THREADS', 'Value': '4'}],
        }


def test_set_batch_overrides_insar_isce_burst_20x4():
    for n in range(1, 23):
        assert lambda_handler(mock_insar_isce_burst_job('20x4', bursts=n), None) == {
            'ResourceRequirements': [
                {
                    'Type': 'MEMORY',
                    'Value': INSAR_ISCE_BURST_MEMORY_8G,
                }
            ],
            'Environment': [{'Name': 'OMP_NUM_THREADS', 'Value': '1'}],
        }
    for n in range(23, 31):
        assert lambda_handler(mock_insar_isce_burst_job('20x4', bursts=n), None) == {
            'ResourceRequirements': [
                {
                    'Type': 'MEMORY',
                    'Value': INSAR_ISCE_BURST_MEMORY_16G,
                }
            ],
            'Environment': [{'Name': 'OMP_NUM_THREADS', 'Value': '2'}],
        }


def test_set_batch_overrides_insar_isce_burst_value_error():
    with pytest.raises(ValueError, match=r'^No memory value for.*'):
        lambda_handler(mock_insar_isce_burst_job('20x4', bursts=31), None)

    with pytest.raises(ValueError, match=r'^No memory value for.*'):
        lambda_handler(mock_insar_isce_burst_job('foo', bursts=1), None)


def test_set_batch_overrides_autorift_s2():
    assert lambda_handler(
        {
            'job_type': 'AUTORIFT',
            'job_parameters': {'granules': ['S2B_']},
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


def test_set_batch_overrides_autorift_landsat():
    assert lambda_handler(
        {
            'job_type': 'AUTORIFT',
            'job_parameters': {'granules': ['LC08_']},
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


def test_set_batch_overrides_rtc_gamma_10m():
    assert lambda_handler(
        {
            'job_type': 'RTC_GAMMA',
            'job_parameters': {'resolution': 10},
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
            'job_parameters': {'resolution': 20},
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


def test_set_batch_overrides_water_map_10m():
    assert lambda_handler(
        {
            'job_type': 'WATER_MAP',
            'job_parameters': {'resolution': 10},
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
            'job_parameters': {'resolution': 20},
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
            'job_parameters': {'resolution': 10},
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
            'job_parameters': {'resolution': 20},
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
