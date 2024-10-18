import argparse
import json
from pathlib import Path
from typing import Optional

import jinja2
import yaml


def snake_to_pascal_case(input_string: str):
    split_string = input_string.lower().split('_')
    return ''.join([i.title() for i in split_string])


def get_states_for_jobs(job_types: dict) -> dict:
    states = {}
    for job_spec in job_types.values():
        states.update(get_states_for_job(job_spec))
    return states


def get_states_for_job(job_spec: dict) -> dict:
    states = {}
    steps = job_spec['steps']
    for i in range(len(steps)):
        step = steps[i]
        next_state_name = steps[i + 1]['name'] if i < len(steps) - 1 else 'GET_FILES'
        states[step['name']] = get_state_for_job_step(step, i, next_state_name, job_spec)
    return states


def get_state_for_job_step(step: dict, index: int, next_state_name: str, job_spec: dict) -> dict:
    if 'map' in step:
        state = get_map_state(job_spec, step)
    else:
        state = get_batch_submit_job_state(job_spec, step, filter_batch_params=True)
    state.update(
        {
            'Catch': [
                {
                    'ErrorEquals': [
                        'States.ALL'
                    ],
                    'ResultPath': f'$.results.processing_results.step_{index}',
                    'Next': 'PROCESSING_FAILED',
                },
            ],
            'ResultPath': f'$.results.processing_results.step_{index}',
            'Next': next_state_name,
        }
    )
    return state


def get_map_state(job_spec: dict, step: dict) -> dict:
    item, items = parse_job_step_map(step['map'])

    batch_job_parameters = get_batch_job_parameters(job_spec, step, map_item=item)

    submit_job_state = get_batch_submit_job_state(job_spec, step)
    submit_job_state['End'] = True
    submit_job_state_name = step['name'] + '_SUBMIT_JOB'
    return {
        'Type': 'Map',
        'ItemsPath': f'$.job_parameters.{items}',
        'ItemSelector': {
            'job_id.$': '$.job_id',
            'priority.$': '$.priority',
            'container_overrides.$': '$.container_overrides',
            'batch_job_parameters': batch_job_parameters,
        },
        'ItemProcessor': {
            'StartAt': submit_job_state_name,
            'States': {
                submit_job_state_name: submit_job_state,
            }
        }
    }


def get_batch_submit_job_state(job_spec: dict, step: dict, filter_batch_params=False) -> dict:
    if filter_batch_params:
        batch_job_parameters = get_batch_job_parameters(job_spec, step)
        parameters_key = 'Parameters'
    else:
        batch_job_parameters = '$.batch_job_parameters'
        parameters_key = 'Parameters.$'

    if 'import' in step['compute_environment']:
        compute_environment = step['compute_environment']['import']
    else:
        compute_environment = step['compute_environment']['name']

    job_queue = 'JobQueueArn' if compute_environment == 'Default' else compute_environment + 'JobQueueArn'
    return {
        'Type': 'Task',
        'Resource': 'arn:aws:states:::batch:submitJob.sync',
        'Parameters': {
            'JobDefinition': '${' + snake_to_pascal_case(step['name']) + '}',
            'JobName.$': '$.job_id',
            'JobQueue': '${' + job_queue + '}',
            'ShareIdentifier': 'default',
            'SchedulingPriorityOverride.$': '$.priority',
            parameters_key: batch_job_parameters,
            'ContainerOverrides.$': '$.container_overrides',
            'RetryStrategy': {
                'Attempts': 3
            },
        },
        'ResultSelector': {
            'start.$': '$.Attempts[*].StartedAt',
            'stop.$': '$.Attempts[*].StoppedAt',
        },
        'Retry': [
            {
                'ErrorEquals': [
                    'Batch.ServerException',
                    'Batch.AWSBatchException'
                ],
                'MaxAttempts': 2
            },
            {
                'ErrorEquals': [
                    'States.ALL'
                ],
                'MaxAttempts': 0
            }
        ]
    }


def parse_job_step_map(step_map: str) -> tuple[str, str]:
    tokens = step_map.split(' ')
    assert len(tokens) == 4
    assert tokens[0], tokens[2] == ('for', 'in')
    return tokens[1], tokens[3]


def get_batch_job_parameters(job_spec: dict, step: dict, map_item: str = None) -> dict:
    job_params = ['bucket_prefix', *job_spec['parameters'].keys()]
    step_params = get_batch_param_names_for_job_step(step)
    batch_params = {
        f'{param}.$': f'$.batch_job_parameters.{param}'
        for param in job_params
        if param in step_params
    }
    if map_item is not None:
        assert map_item in step_params
        batch_params[f'{map_item}.$'] = '$$.Map.Item.Value'
    return batch_params


def get_batch_param_names_for_job_step(step: dict) -> set[str]:
    ref_prefix = 'Ref::'
    return {
        arg.removeprefix(ref_prefix)
        for arg in step['command']
        if arg.startswith(ref_prefix)
    }


def render_templates(job_types, compute_envs, security_environment, api_name):
    job_states = get_states_for_jobs(job_types)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('./'),
        autoescape=jinja2.select_autoescape(default=True, disabled_extensions=('j2',)),
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        extensions=['jinja2.ext.do'],
    )

    for template_file in Path('.').glob('**/*.j2'):
        template = env.get_template(str(template_file))

        output = template.render(
            job_types=job_types,
            compute_envs=compute_envs,
            compute_env_names=[env['name'] for env in compute_envs],
            security_environment=security_environment,
            api_name=api_name,
            json=json,
            snake_to_pascal_case=snake_to_pascal_case,
            job_states=job_states,
        )

        if str(template_file).endswith('.json.j2'):
            output = json.dumps(json.loads(output), indent=2)

        template_file.with_suffix('').write_text(output)


def get_compute_environments(job_types: dict, compute_env_file: Optional[Path]) -> list[dict]:
    compute_envs = []
    compute_env_names = set()
    compute_env_imports = set()
    for _, job_spec in job_types.items():
        for step in job_spec['steps']:
            compute_env = step['compute_environment']
            if 'name' in compute_env:
                name = compute_env['name']
                assert name != 'Default'
                if name in compute_env_names:
                    raise ValueError(
                        f'Compute envs must have unique names but the following is defined more than once: {name}.'
                    )
                compute_envs.append(compute_env)
                compute_env_names.add(name)
            elif 'import' in compute_env and compute_env['import'] != 'Default':
                compute_env_imports.add(compute_env['import'])
            else:
                assert compute_env['import'] == 'Default'

    if compute_env_file:
        compute_envs_from_file = yaml.safe_load(compute_env_file.read_text())['compute_environments']
        for name in compute_envs_from_file:
            assert name != 'Default'
            if name in compute_env_names:
                raise ValueError(
                    f'Compute envs must have unique names but the following is defined more than once: {name}.'
                )
            compute_env = compute_envs_from_file[name]
            compute_env['name'] = name
            compute_envs.append(compute_env)
            compute_env_names.add(name)

    for name in compute_env_imports:
        if name not in compute_envs_from_file:
            raise ValueError(
                f'The following compute env is imported but not defined in the compute envs file: {name}.'
            )

    return compute_envs


def render_batch_params_by_job_type(job_types: dict) -> None:
    batch_params_by_job_type = {}
    for job_type, job_spec in job_types.items():
        params = set()
        for step in job_spec['steps']:
            params.update(get_batch_param_names_for_job_step(step))
        batch_params_by_job_type[job_type] = list(params)
    with (Path('apps') / 'start-execution-worker' / 'src' / 'batch_params_by_job_type.json').open('w') as f:
        json.dump(batch_params_by_job_type, f, indent=2)


def render_default_params_by_job_type(job_types: dict) -> None:
    default_params_by_job_type = {
        job_type: {
            key: value['api_schema']['default'] for key, value in job_spec['parameters'].items()
            if key not in job_spec['required_parameters']
        }
        for job_type, job_spec in job_types.items()
    }
    with open(Path('lib') / 'dynamo' / 'dynamo' / 'default_params_by_job_type.json', 'w') as f:
        json.dump(default_params_by_job_type, f, indent=2)


def render_costs(job_types: dict, cost_profile: str) -> None:
    costs = [
        {
            'job_type': job_type,
            **job_spec['cost_profiles'][cost_profile],
        }
        for job_type, job_spec in job_types.items()
    ]
    with open(Path('lib') / 'dynamo' / 'dynamo' / 'costs.json', 'w') as f:
        json.dump(costs, f, indent=2)


def validate_job_spec(job_type: str, job_spec: dict) -> None:
    expected_fields = sorted(['required_parameters', 'parameters', 'cost_profiles', 'validators', 'steps'])
    actual_fields = sorted(job_spec.keys())
    if actual_fields != expected_fields:
        raise ValueError(f'{job_type} has fields {actual_fields} but should have {expected_fields}')

    reserved_params = {'bucket_prefix'}
    reserved_params_in_spec = reserved_params.intersection(set(job_spec['parameters'].keys()))
    if reserved_params_in_spec:
        raise ValueError(f'{job_type} contains reserved parameter names: {sorted(reserved_params_in_spec)}')

    expected_param_fields = ['api_schema']
    for param_name, param_dict in job_spec['parameters'].items():
        actual_param_fields = sorted(param_dict.keys())
        if actual_param_fields != expected_param_fields:
            raise ValueError(
                f"parameter '{param_name}' for {job_type} has fields {actual_param_fields} "
                f"but should have {expected_param_fields}"
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-j', '--job-spec-files', required=True, nargs='+', type=Path)
    parser.add_argument('-e', '--compute-environment-file', type=Path)
    parser.add_argument('-s', '--security-environment', default='ASF', choices=['ASF', 'EDC', 'JPL', 'JPL-public'])
    parser.add_argument('-n', '--api-name', required=True)
    parser.add_argument('-c', '--cost-profile', default='DEFAULT', choices=['DEFAULT', 'EDC'])
    args = parser.parse_args()

    job_types = {}
    for file in args.job_spec_files:
        job_types.update(yaml.safe_load(file.read_text()))

    for job_type, job_spec in job_types.items():
        validate_job_spec(job_type, job_spec)

    for job_type, job_spec in job_types.items():
        for step in job_spec['steps']:
            step['name'] = job_type + '_' + step['name'] if step['name'] else job_type

    compute_envs = get_compute_environments(job_types, args.compute_environment_file)

    render_batch_params_by_job_type(job_types)
    render_default_params_by_job_type(job_types)
    render_costs(job_types, args.cost_profile)
    render_templates(job_types, compute_envs, args.security_environment, args.api_name)


if __name__ == '__main__':
    main()
