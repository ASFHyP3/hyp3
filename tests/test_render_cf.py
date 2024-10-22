import pytest
import render_cf
import yaml


def test_parse_map_statement():
    assert render_cf.parse_map_statement('for item in items') == ('item', 'items')
    assert render_cf.parse_map_statement('for foo in bar') == ('foo', 'bar')

    with pytest.raises(ValueError, match='expected 4 tokens in map statement but got 3: item in items'):
        render_cf.parse_map_statement('item in items')

    with pytest.raises(ValueError, match='expected 4 tokens in map statement but got 5: for for item in items'):
        render_cf.parse_map_statement('for for item in items')

    with pytest.raises(ValueError, match="expected 'for', got 'fr': fr item in items"):
        render_cf.parse_map_statement('fr item in items')

    with pytest.raises(ValueError, match="expected 'in', got 'ib': for item ib items"):
        render_cf.parse_map_statement('for item ib items')


def test_get_batch_job_parameters():
    assert False


def test_get_batch_param_names_for_job_step():
    assert False


def test_get_compute_environments(tmp_path):
    job_types = {
        'FOO': {
            'steps': [
                {'compute_environment': 'ComputeEnvironment1'},
                {'compute_environment': 'Default'},
            ],
        },
        'BAR': {
            'steps': [
                {'compute_environment': 'ComputeEnvironment2'},
            ],
        },
        'BAZ': {
            'steps': [
                {'compute_environment': 'ComputeEnvironment1'},
                {'compute_environment': 'ComputeEnvironment2'},
            ],
        },
    }
    compute_env_file_contents = {
        'compute_environments': {
            'ComputeEnvironment1': {'key1': 'value1'},
            'ComputeEnvironment2': {'key2': 'value2'},
            'ComputeEnvironment3': {'key3': 'value3'},
        }
    }
    expected_compute_envs = {
        'ComputeEnvironment1': {'key1': 'value1'},
        'ComputeEnvironment2': {'key2': 'value2'},
    }
    compute_env_file = tmp_path / 'compute_environments.yml'
    yaml.dump(compute_env_file_contents, open(compute_env_file, 'w'))
    assert render_cf.get_compute_environments_for_deployment(job_types, compute_env_file) == expected_compute_envs

    compute_env_file_contents = {
        'compute_environments': {
            'ComputeEnvironment1': {'key1': 'value1'},
            'ComputeEnvironment2': {'key2': 'value2'},
            'ComputeEnvironment3': {'key3': 'value3'},
            'Default': {'key', 'value'},
        }
    }
    yaml.dump(compute_env_file_contents, open(compute_env_file, 'w'))
    with pytest.raises(ValueError, match="'Default' is a reserved compute environment name"):
        render_cf.get_compute_environments_for_deployment(job_types, compute_env_file)

    compute_env_file_contents = {
        'compute_environments': {
            'ComputeEnvironment1': {'key1': 'value1'},
        }
    }
    yaml.dump(compute_env_file_contents, open(compute_env_file, 'w'))
    with pytest.raises(KeyError, match='ComputeEnvironment2'):
        render_cf.get_compute_environments_for_deployment(job_types, compute_env_file)
