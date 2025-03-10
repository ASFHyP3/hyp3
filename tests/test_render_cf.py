from pathlib import Path

import pytest
import yaml

import render_cf


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

    with pytest.raises(
        ValueError, match="map statement contains reserved parameter name 'job_id': for job_id in items"
    ):
        render_cf.parse_map_statement('for job_id in items')


def test_get_batch_job_parameters():
    job_spec: dict = {'parameters': {'param1': {}, 'param2': {}, 'param3': {}, 'param4': {}}}

    step = {'command': ['foo', 'Ref::param2', 'Ref::param3', 'bar', 'Ref::job_id']}
    assert render_cf.get_batch_job_parameters(job_spec, step) == {
        'param2.$': '$.batch_job_parameters.param2',
        'param3.$': '$.batch_job_parameters.param3',
        'job_id.$': '$.job_id',
    }

    step = {'command': ['foo', 'Ref::param2', 'Ref::param3', 'bar', 'Ref::param5']}
    assert render_cf.get_batch_job_parameters(job_spec, step, map_item='param5') == {
        'param2.$': '$.batch_job_parameters.param2',
        'param3.$': '$.batch_job_parameters.param3',
        'param5.$': "States.Format('{}', $$.Map.Item.Value)",
    }

    step = {'command': ['foo', 'Ref::param2', 'Ref::param3', 'bar', 'Ref::param5']}
    with pytest.raises(ValueError, match="job parameter 'param5' has not been defined"):
        render_cf.get_batch_job_parameters(job_spec, step)


def test_get_batch_param_names_for_job_step():
    step = {'command': ['param1', 'Ref::param2', 'Ref::param3', 'Ref::param2', 'param4', 'Ref::param5']}
    assert render_cf.get_batch_param_names_for_job_step(step) == {'param2', 'param3', 'param5'}


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
    compute_env_file_contents: dict = {
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
    yaml.dump(compute_env_file_contents, Path(compute_env_file).open('w'))
    assert render_cf.get_compute_environments_for_deployment(job_types, compute_env_file) == expected_compute_envs

    compute_env_file_contents = {
        'compute_environments': {
            'ComputeEnvironment1': {'key1': 'value1'},
            'ComputeEnvironment2': {'key2': 'value2'},
            'ComputeEnvironment3': {'key3': 'value3'},
            'Default': {'key', 'value'},
        }
    }
    yaml.dump(compute_env_file_contents, Path(compute_env_file).open('w'))
    with pytest.raises(ValueError, match="'Default' is a reserved compute environment name"):
        render_cf.get_compute_environments_for_deployment(job_types, compute_env_file)

    compute_env_file_contents = {
        'compute_environments': {
            'ComputeEnvironment1': {'key1': 'value1'},
        }
    }
    yaml.dump(compute_env_file_contents, Path(compute_env_file).open('w'))
    with pytest.raises(KeyError, match='ComputeEnvironment2'):
        render_cf.get_compute_environments_for_deployment(job_types, compute_env_file)


def test_validate_job_spec():
    job_type = 'FOO'
    job_spec = {
        'required_parameters': ['granules'],
        'parameters': {'foo': {'api_schema': {}}},
        'cost_profiles': {
            'foo': {'cost': 10},
            'bar': {
                'cost_parameters': ['param1', 'param2'],
                'cost_table': {'param1-value': {'param2-value': 1.0}}
            }
        },
        'validators': [],
        'steps': [
            {
                'image': 'repo/hyp3-gamma',
            },
            {
                'image': 'repo/water-map-equal-percent-solution',
            },
        ],
    }

    render_cf.validate_job_spec(job_type, job_spec)

    fields_error_message = r'^FOO has fields .* but should have .*'
    with pytest.raises(ValueError, match=fields_error_message):
        job_spec_missing_field = {**job_spec}
        del job_spec_missing_field['required_parameters']

        render_cf.validate_job_spec(job_type, job_spec_missing_field)

    with pytest.raises(ValueError, match=fields_error_message):
        job_spec_missing_field = {**job_spec}
        del job_spec_missing_field['parameters']

        render_cf.validate_job_spec(job_type, job_spec_missing_field)

    with pytest.raises(ValueError, match=fields_error_message):
        job_spec_missing_field = {**job_spec}
        del job_spec_missing_field['cost_profiles']

        render_cf.validate_job_spec(job_type, job_spec_missing_field)

    with pytest.raises(ValueError, match=fields_error_message):
        job_spec_missing_field = {**job_spec}
        del job_spec_missing_field['validators']

        render_cf.validate_job_spec(job_type, job_spec_missing_field)

    with pytest.raises(ValueError, match=fields_error_message):
        job_spec_missing_field = {**job_spec}
        del job_spec_missing_field['steps']

        render_cf.validate_job_spec(job_type, job_spec_missing_field)

    with pytest.raises(ValueError, match=fields_error_message):
        job_spec_bad_field = {**job_spec, 'bad_field': ''}
        render_cf.validate_job_spec(job_type, job_spec_bad_field)

    with pytest.raises(ValueError, match=r"^FOO contains reserved parameter name 'job_id'$"):
        job_spec_with_job_id_param = {**job_spec, 'parameters': {'job_id': {'api_schema': {}}}}
        render_cf.validate_job_spec(job_type, job_spec_with_job_id_param)

    param_fields_error_message = r"^parameter 'foo' for FOO has fields .* but should have .*"
    with pytest.raises(ValueError, match=param_fields_error_message):
        job_spec_missing_param_field = {**job_spec, 'parameters': {'foo': {}}}
        render_cf.validate_job_spec(job_type, job_spec_missing_param_field)

    with pytest.raises(ValueError, match=param_fields_error_message):
        job_spec_bad_param_field = {**job_spec, 'parameters': {'foo': {'api_schema': {}, 'bad_field': ''}}}
        render_cf.validate_job_spec(job_type, job_spec_bad_param_field)

    job_spec_uppercase_image = {
        **job_spec,
        'steps': [
            {
                'image': 'repo/HyP3-gamma',
            },
        ],
    }
    with pytest.raises(
        ValueError, match=r'^FOO has image repo/HyP3-gamma but docker requires the image to be all lowercase.*'
    ):
        render_cf.validate_job_spec(job_type, job_spec_uppercase_image)

    bad_cost_profile_error = '^Cost definition for job type FOO has invalid keys: dict_keys.*'
    with pytest.raises(ValueError, match=bad_cost_profile_error):
        job_spec_bad_cost_profile = {**job_spec, 'cost_profiles': {'foo': {}}}
        render_cf.validate_job_spec(job_type, job_spec_bad_cost_profile)

    bad_cost_profile_error = '^Cost definition for job type FOO has empty cost_table'
    with pytest.raises(ValueError, match=bad_cost_profile_error):
        job_spec_bad_cost_profile = {**job_spec, 'cost_profiles': {
            'foo': {'cost_parameters': ['param1', 20], 'cost_table': {}}
        }}
        render_cf.validate_job_spec(job_type, job_spec_bad_cost_profile)

    bad_cost_profile_error = r'.*all cost_table keys must be strings or ints, but \(1, 2\) has type <class \'tuple\'>'
    with pytest.raises(ValueError, match=bad_cost_profile_error):
        job_spec_bad_cost_profile = {**job_spec, 'cost_profiles': {
            'foo': {'cost_parameters': ['param1', 20], 'cost_table': {(1, 2): {'x'}}}}
        }
        render_cf.validate_job_spec(job_type, job_spec_bad_cost_profile)

    bad_cost_profile_error = r'Cost table must be a nested dictionary of costs, got type <class \'str\'>'
    with pytest.raises(ValueError, match=bad_cost_profile_error):
        job_spec_bad_cost_profile = {**job_spec, 'cost_profiles': {
            'foo': {'cost_parameters': ['param1', 20], 'cost_table': {'x': 'y'}}
        }}
        render_cf.validate_job_spec(job_type, job_spec_bad_cost_profile)
