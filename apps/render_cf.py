import argparse
import json
from pathlib import Path
from typing import Optional

import jinja2
import yaml


def snake_to_pascal_case(input_string: str):
    split_string = input_string.lower().split('_')
    return ''.join([i.title() for i in split_string])


def get_steps_for_jobs(job_types: dict) -> dict:
    steps = {}
    for job_spec in job_types.values():
        steps.update(get_steps_for_job(job_spec))
    return steps


def get_steps_for_job(job_spec: dict) -> dict:
    steps = {}
    tasks = job_spec['tasks']
    for i in range(len(tasks)):
        task = tasks[i]
        next_step_name = tasks[i + 1]['name'] if i < len(tasks) - 1 else 'GET_FILES'
        steps[task['name']] = get_step_for_task(task, i, next_step_name, job_spec)
    return steps


def get_step_for_task(task: dict, index: int, next_step_name: str, job_spec: dict) -> dict:
    if 'map' in task:
        step = get_step_for_map_task(task, job_spec)
    else:
        step = get_step_for_batch_submit_job(task)
    step.update(
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
            'Next': next_step_name,
        }
    )
    return step


def get_step_for_map_task(task: dict, job_spec: dict) -> dict:
    item, items = parse_task_map(task['map'])
    job_parameters = get_job_parameters(item, items, job_spec)
    submit_job_step = get_step_for_batch_submit_job(task)
    submit_job_step['End'] = True
    submit_job_step_name = task['name'] + '_SUBMIT_JOB'
    return {
        'Type': 'Map',
        'ItemsPath': f'$.original_job_parameters.{items}',
        'ItemSelector': {
            'job_id.$': '$.job_id',
            'priority.$': '$.priority',
            'container_overrides.$': '$.container_overrides',
            'job_parameters': job_parameters,
        },
        'ItemProcessor': {
            'StartAt': submit_job_step_name,
            'States': {
                submit_job_step_name: submit_job_step,
            }
        }
    }


def parse_task_map(task_map: str) -> tuple[str, str]:
    tokens = task_map.split(' ')
    assert len(tokens) == 4
    assert tokens[0], tokens[2] == ('for', 'in')
    return tokens[1], tokens[3]


def get_job_parameters(item: str, items: str, job_spec: dict) -> dict:
    job_parameters = {
        f'{param}.$': f'$.job_parameters.{param}'
        for param in job_spec['parameters']
        if param != items
    }
    job_parameters[f'{item}.$'] = '$$.Map.Item.Value'
    return job_parameters


def get_step_for_batch_submit_job(task: dict) -> dict:
    if 'import' in task['compute_environment']:
        compute_environment = task['compute_environment']['import']
    else:
        compute_environment = task['compute_environment']['name']
    job_queue = compute_environment + 'JobQueueArn'
    return {
        'Type': 'Task',
        'Resource': 'arn:aws:states:::batch:submitJob.sync',
        'Parameters': {
            'JobDefinition': '${'+ snake_to_pascal_case(task['name']) + '}',
            'JobName.$': '$.job_id',
            'JobQueue': '${' + job_queue + '}',
            'ShareIdentifier': 'default',
            'SchedulingPriorityOverride.$': '$.priority',
            'Parameters.$': '$.job_parameters',
            'ContainerOverrides.$': '$.container_overrides',
            'RetryStrategy': {
                'Attempts': 3
            },
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


def render_templates(job_types, compute_envs, security_environment, api_name):
    job_steps = get_steps_for_jobs(job_types)

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
            job_steps=job_steps,
        )

        if str(template_file).endswith('.json.j2'):
            output = json.dumps(json.loads(output), indent=2)

        template_file.with_suffix('').write_text(output)


def get_compute_environments(job_types: dict, compute_env_file: Optional[Path]) -> list[dict]:
    compute_envs = []
    compute_env_names = set()
    compute_env_imports = set()
    for _, job_spec in job_types.items():
        for task in job_spec['tasks']:
            compute_env = task['compute_environment']
            if 'name' in compute_env:
                name = compute_env['name']
                if name in compute_env_names:
                    raise ValueError(
                        f'Compute envs must have unique names but the following is defined more than once: {name}.'
                    )
                compute_envs.append(compute_env)
                compute_env_names.add(name)
            elif 'import' in compute_env:
                compute_env_imports.add(compute_env['import'])
            else:
                raise ValueError(
                    f'The compute env must be defined with `name` or be imported with `import`.'
                )

    if compute_env_file:
        compute_envs_from_file = yaml.safe_load(compute_env_file.read_text())['compute_environments']
        for name in compute_envs_from_file:
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


def render_default_params_by_job_type(job_types: dict) -> None:
    default_params_by_job_type = {
        job_type: {
            key: value['api_schema']['default'] for key, value in job_spec['parameters'].items()
            if key not in job_spec['required_parameters'] and 'api_schema' in value
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
        for task in job_spec['tasks']:
            task['name'] = job_type + '_' + task['name'] if task['name'] else job_type

    compute_envs = get_compute_environments(job_types, args.compute_environment_file)

    render_default_params_by_job_type(job_types)
    render_costs(job_types, args.cost_profile)
    render_templates(job_types, compute_envs, args.security_environment, args.api_name)


if __name__ == '__main__':
    main()
