import yaml

import render_cf

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
            'compute_environment_4': {
                'instance_types': ['type_4']
            }
        }
    }
    compute_env_filepath = tmp_path / 'compute_environments.yml'
    yaml.dump(compute_env_file, open(compute_env_filepath, 'w'))

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
    compute_envs = render_cf.get_compute_environments(job_types, compute_env_filepath)
    assert compute_envs == expected_compute_envs

    #TODO: Invalid Case
