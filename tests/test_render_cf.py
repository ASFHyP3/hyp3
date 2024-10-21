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
    # TODO update
    job_types = {
        'FOO': {
            'steps': [
                {
                    'compute_environment': {
                        'name': 'compute_environment_1',
                        'intance_types': ['type1', 'type2']
                    }
                },
                {'compute_environment': {'import': 'Default'}}
            ]
        },
        'BAR': {
            'steps': [
                {'compute_environment': {'import': 'compute_environment_2'}},
                {
                    'compute_environment': {
                        'name': 'compute_environment_3',
                        'allocation_type': 'alloc_type_1',
                        'allocation_strategy': 'alloc_strat_1'
                    }
                }
            ]
        }
    }
    compute_env_file = {
        'compute_environments': {
            'compute_environment_2': {
                'instance_types': ['type_3'],
                'ami_id': 'ami_id_1',
                'allocation_type': 'alloc_type_2',
                'allocation_strategy': 'alloc_strat_2'
            },
            'compute_environment_4': {'instance_types': ['type_4']}
        }
    }
    expected_compute_envs = [
        {
            'name': 'compute_environment_1',
            'intance_types': ['type1', 'type2']
        },
        {
            'name': 'compute_environment_3',
            'allocation_type': 'alloc_type_1',
            'allocation_strategy': 'alloc_strat_1'
        },
        {
            'name': 'compute_environment_2',
            'instance_types': ['type_3'],
            'ami_id': 'ami_id_1',
            'allocation_type': 'alloc_type_2',
            'allocation_strategy': 'alloc_strat_2'
        }
    ]
    compute_env_filepath = tmp_path / 'compute_environments.yml'
    yaml.dump(compute_env_file, open(compute_env_filepath, 'w'))
    compute_envs = render_cf.get_compute_environments(job_types, compute_env_filepath)
    assert compute_envs == expected_compute_envs

    job_types_redefined_default = {
        'FOO': {'steps': [{'compute_environment': {'name': 'Default'}}]}}
    with pytest.raises(ValueError, match=r'.*defined more than once: Default*'):
        compute_envs = render_cf.get_compute_environments(job_types_redefined_default)

    job_types_duplicate_env = {
        'FOO': {'steps': [{'compute_environment': {'name': 'compute_environment_1'}}]},
        'BAR': {'steps': [{'compute_environment': {'name': 'compute_environment_1'}}]}
    }
    with pytest.raises(ValueError, match=r'.*defined more than once: compute_environment_1*'):
        compute_envs = render_cf.get_compute_environments(job_types_duplicate_env)

    job_types_import_undefined = {
        'FOO': {'steps': [{'compute_environment': {'import': 'undefined_compute_environment'}}]}
    }
    with pytest.raises(ValueError, match=r'.*not defined in the compute envs file: undefined_compute_environment*'):
        compute_envs = render_cf.get_compute_environments(job_types_import_undefined, compute_env_filepath)
    with pytest.raises(ValueError, match=r'.*no compute env file was provided: {\'undefined_compute_environment\'}*'):
        compute_envs = render_cf.get_compute_environments(job_types_import_undefined)

    compute_env_file_redefined_default = {'compute_environments': {'Default': {}}}
    yaml.dump(compute_env_file_redefined_default, open(compute_env_filepath, 'w'))
    with pytest.raises(ValueError, match=r'.*defined more than once: Default*'):
        compute_envs = render_cf.get_compute_environments(job_types, compute_env_filepath)

    job_types = {
        'FOO': {
            'steps': [
                {'compute_environment': {'name': 'compute_environment_1'}},
                {'compute_environment': {'import': 'compute_environment_1'}}
            ]
        }
    }
    compute_env_file_duplicate = {'compute_environments': {'compute_environment_1': {}}}
    yaml.dump(compute_env_file_duplicate, open(compute_env_filepath, 'w'))
    with pytest.raises(ValueError, match=r'.*defined more than once: compute_environment_1*'):
        compute_envs = render_cf.get_compute_environments(job_types, compute_env_filepath)
