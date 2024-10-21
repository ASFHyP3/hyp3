import pytest
import render_cf
import yaml


def test_get_compute_environments(tmp_path):
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
