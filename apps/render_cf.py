import argparse
import json
from pathlib import Path

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
    tasks = job_spec["tasks"]
    for i in range(len(tasks)):
        task = tasks[i]
        next_step_name = tasks[i + 1]["name"] if i < len(tasks) - 1 else "GET_FILES"
        steps[task["name"]] = get_step_for_task(task, i, next_step_name, job_spec)
    return steps


def get_step_for_task(task: dict, index: int, next_step_name: str, job_spec: dict) -> dict:
    if "map" in task:
        return get_step_for_map_task(task, index, next_step_name, job_spec)
    return get_step_for_normal_task(task, index, next_step_name, job_spec)


def get_step_for_normal_task(task: dict, index: int, next_step_name: str, job_spec: dict) -> dict:
    compute_environment = job_spec["compute_environment"]["name"]
    job_queue = "JobQueueArn" if compute_environment == "Default" else compute_environment + "JobQueueArn"
    return {
        "Type": "Task",
        "Resource": "arn:aws:states:::batch:submitJob.sync",
        "Parameters": {
            "JobDefinition": "${"+ snake_to_pascal_case(task["name"]) + "}",
            "JobName.$": "$.job_id",
            "JobQueue": "${" + job_queue + "}",
            "ShareIdentifier": "default",
            "SchedulingPriorityOverride.$": "$.priority",
            "Parameters.$": "$.job_parameters",
            "ContainerOverrides.$": "$.container_overrides",
            "RetryStrategy": {
                "Attempts": 3
            },
        },
        "ResultPath": f"$.results.processing_results.step_{index}",
        "Next": next_step_name,
        "Retry": [
            {
                "ErrorEquals": [
                    "Batch.ServerException",
                    "Batch.AWSBatchException"
                ],
                "MaxAttempts": 2
            },
            {
                "ErrorEquals": [
                    "States.ALL"
                ],
                "MaxAttempts": 0
            }
        ],
        "Catch": [
            {
                "ErrorEquals": [
                    "States.ALL"
                ],
                "Next": "PROCESSING_FAILED",
                "ResultPath": f"$.results.processing_results.step_{index}"
            }
        ],
    }


def get_step_for_map_task(task: dict, index: int, next_step_name: str, job_spec: dict) -> dict:
    # TODO
    pass


def render_templates(job_types, security_environment, api_name):
    job_steps = get_steps_for_jobs(job_types)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('./'),
        autoescape=jinja2.select_autoescape(default=True, disabled_extensions=('j2',)),
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    for template_file in Path('.').glob('**/*.j2'):
        template = env.get_template(str(template_file))

        output = template.render(
            job_types=job_types,
            security_environment=security_environment,
            api_name=api_name,
            json=json,
            snake_to_pascal_case=snake_to_pascal_case,
            job_steps=job_steps,
        )

        if str(template_file).endswith('.json.j2'):
            output = json.dumps(json.loads(output), indent=2)

        template_file.with_suffix('').write_text(output)


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

    render_default_params_by_job_type(job_types)
    render_costs(job_types, args.cost_profile)
    render_templates(job_types, args.security_environment, args.api_name)


if __name__ == '__main__':
    main()
