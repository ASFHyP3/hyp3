import argparse
import json
from pathlib import Path

import jinja2
import yaml


def snake_to_pascal_case(input_string: str) -> str:
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
                    'ErrorEquals': ['States.ALL'],
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
    item, items = parse_map_statement(step['map'])

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
            },
        },
    }


def get_batch_submit_job_state(job_spec: dict, step: dict, filter_batch_params: bool = False) -> dict:
    if filter_batch_params:
        batch_job_parameters: dict | str = get_batch_job_parameters(job_spec, step)
        parameters_key = 'Parameters'
    else:
        batch_job_parameters = '$.batch_job_parameters'
        parameters_key = 'Parameters.$'

    compute_environment = step['compute_environment']
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
            'RetryStrategy': {'Attempts': 3},
        },
        'ResultSelector': {
            'StartedAt.$': '$.StartedAt',
            'StoppedAt.$': '$.StoppedAt',
        },
        'Retry': [
            {'ErrorEquals': ['Batch.ServerException', 'Batch.AWSBatchException'], 'MaxAttempts': 2},
            {'ErrorEquals': ['States.ALL'], 'MaxAttempts': 0},
        ],
    }


def parse_map_statement(map_statement: str) -> tuple[str, str]:
    tokens = map_statement.split(' ')
    if len(tokens) != 4:
        raise ValueError(f'expected 4 tokens in map statement but got {len(tokens)}: {map_statement}')
    if tokens[0] != 'for':
        raise ValueError(f"expected 'for', got '{tokens[0]}': {map_statement}")
    if tokens[2] != 'in':
        raise ValueError(f"expected 'in', got '{tokens[2]}': {map_statement}")
    item, items = tokens[1], tokens[3]
    if item == 'job_id':
        raise ValueError(f"map statement contains reserved parameter name 'job_id': {map_statement}")
    return item, items


def get_batch_job_parameters(job_spec: dict, step: dict, map_item: str | None = None) -> dict:
    step_params = get_batch_param_names_for_job_step(step)
    batch_params = {}
    for param in step_params:
        if param == 'job_id':
            batch_params['job_id.$'] = '$.job_id'
        elif param == map_item:
            batch_params[f'{map_item}.$'] = "States.Format('{}', $$.Map.Item.Value)"
        else:
            if param not in job_spec['parameters']:
                raise ValueError(f"job parameter '{param}' has not been defined")
            batch_params[f'{param}.$'] = f'$.batch_job_parameters.{param}'
    return batch_params


def get_batch_param_names_for_job_step(step: dict) -> set[str]:
    ref_prefix = 'Ref::'
    return {arg.removeprefix(ref_prefix) for arg in step['command'] if arg.startswith(ref_prefix)}


def render_templates(job_types: dict, compute_envs: dict, security_environment: str, api_name: str) -> None:
    job_states = get_states_for_jobs(job_types)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('./'),
        autoescape=jinja2.select_autoescape(default=True, disabled_extensions=('j2',)),
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    for template_file in Path().glob('**/*.j2'):
        template = env.get_template(str(template_file))

        output = template.render(
            job_types=job_types,
            compute_envs=compute_envs,
            security_environment=security_environment,
            api_name=api_name,
            json=json,
            snake_to_pascal_case=snake_to_pascal_case,
            job_states=job_states,
        )

        if str(template_file).endswith('.json.j2'):
            output = json.dumps(json.loads(output), indent=2)

        template_file.with_suffix('').write_text(output)


def get_compute_environments_for_deployment(job_types: dict, compute_env_file: Path) -> dict:
    compute_envs = yaml.safe_load(compute_env_file.read_text())['compute_environments']

    if 'Default' in compute_envs:
        raise ValueError("'Default' is a reserved compute environment name")

    return {
        step['compute_environment']: compute_envs[step['compute_environment']]
        for job_spec in job_types.values()
        for step in job_spec['steps']
        if step['compute_environment'] != 'Default'
    }


def render_batch_params_by_job_type(job_types: dict) -> None:
    batch_params_by_job_type = {}
    for job_type, job_spec in job_types.items():
        params = set()
        for step in job_spec['steps']:
            params.update(get_batch_param_names_for_job_step(step))
        batch_params_by_job_type[job_type] = list(params)
    with (Path('apps') / 'start-execution' / 'src' / 'batch_params_by_job_type.json').open('w') as f:
        json.dump(batch_params_by_job_type, f, indent=2)


def render_default_params_by_job_type(job_types: dict) -> None:
    default_params_by_job_type = {
        job_type: {
            key: value['api_schema']['default']
            for key, value in job_spec['parameters'].items()
            if key not in job_spec['required_parameters']
        }
        for job_type, job_spec in job_types.items()
    }
    with (Path('lib') / 'dynamo' / 'dynamo' / 'default_params_by_job_type.json').open('w') as f:
        json.dump(default_params_by_job_type, f, indent=2)


def render_costs(job_types: dict, cost_profile: str) -> None:
    costs = {job_type: job_spec['cost_profiles'][cost_profile] for job_type, job_spec in job_types.items()}

    with (Path('lib') / 'dynamo' / 'dynamo' / 'costs.json').open('w') as f:
        json.dump(costs, f, indent=2)


def validate_job_spec(job_type: str, job_spec: dict) -> None:
    expected_fields = sorted(['required_parameters', 'parameters', 'cost_profiles', 'validators', 'steps'])
    actual_fields = sorted(job_spec.keys())
    if actual_fields != expected_fields:
        raise ValueError(f'{job_type} has fields {actual_fields} but should have {expected_fields}')

    if 'job_id' in job_spec['parameters']:
        raise ValueError(f"{job_type} contains reserved parameter name 'job_id'")

    expected_param_fields = ['api_schema']
    for param_name, param_dict in job_spec['parameters'].items():
        actual_param_fields = sorted(param_dict.keys())
        if actual_param_fields != expected_param_fields:
            raise ValueError(
                f"parameter '{param_name}' for {job_type} has fields {actual_param_fields} "
                f'but should have {expected_param_fields}'
            )

    for profile in job_spec['cost_profiles'].values():
        if profile.keys() not in ({'cost_parameters', 'cost_table'}, {'cost'}):
            raise ValueError(f'Cost definition for job type {job_type} has invalid keys: {profile.keys()}')

        if 'cost_table' in profile:
            if not isinstance(profile['cost_parameters'], list):
                raise ValueError(
                    f'Cost definition for job type {job_type} has invalid cost_parameters: Must be a list of strings.'
                )

            validate_cost_table(profile['cost_table'], job_type)

    for step in job_spec['steps']:
        if not step['image'].islower():
            raise ValueError(f'{job_type} has image {step["image"]} but docker requires the image to be all lowercase')


def validate_cost_table(cost_table: any, job_type: dict) -> any:
    if isinstance(cost_table, dict):
        for key, value in cost_table.items():
            if not isinstance(key, str) and not isinstance(key, int):
                raise ValueError(
                    f'Cost definition for job type {job_type} has invalid cost_table: '
                    f'all cost_table keys must be strings or ints {type(key)}.'
                )

            return validate_cost_table(value, job_type)

    elif isinstance(cost_table, float):
        if not cost_table.is_integer():
            raise ValueError(
                f'Cost definition for job type {job_type} has invalid cost_table: '
                'all cost_table costs must be whole numbers.'
            )

        return

    else:
        raise ValueError(
            f'Cost definition for job type {job_type} has invalid cost_table: '
            f'Cost table must be a nested dictionary of costs. {type(cost_table)}'
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('-j', '--job-spec-files', required=True, nargs='+', type=Path)
    parser.add_argument('-e', '--compute-environment-file', required=True, type=Path)
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

    compute_envs = get_compute_environments_for_deployment(job_types, args.compute_environment_file)

    render_batch_params_by_job_type(job_types)
    render_default_params_by_job_type(job_types)
    render_costs(job_types, args.cost_profile)
    render_templates(job_types, compute_envs, args.security_environment, args.api_name)


if __name__ == '__main__':
    main()
