import argparse
import json
from pathlib import Path

import jinja2
import yaml


def snake_to_pascal_case(input_string: str):
    split_string = input_string.lower().split('_')
    return ''.join([i.title() for i in split_string])


def render_templates(job_types, security_environment, api_name):
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
        )

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
    costs = {
        job_type: get_cost_dict(job_spec, cost_profile)
        for job_type, job_spec in job_types.items()
    }
    # FIXME: json requires keys to be strings, so e.g. RTC resolution gets converted to str
    with open(Path('lib') / 'dynamo' / 'dynamo' / 'costs.json', 'w') as f:
        json.dump(costs, f, indent=2)


def get_cost_dict(job_spec: dict, cost_profile: str) -> dict:
    keys = job_spec.keys()

    # TODO delete this case after all job specs have cost definitions
    if 'cost_parameter' not in keys and 'cost_tables' not in keys and 'default_cost' not in keys:
        return {'default_cost': 99999999.0}

    if 'cost_parameter' in keys:
        assert 'cost_tables' in keys and 'default_cost' not in keys
        return {
            'cost_parameter': job_spec['cost_parameter'],
            'cost_table': job_spec['cost_tables'][cost_profile],
        }
    assert 'default_cost' in keys and 'cost_tables' not in keys
    return {'default_cost': job_spec['default_cost']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-j', '--job-spec-files', required=True, nargs='+', type=Path)
    parser.add_argument('-s', '--security-environment', default='ASF', choices=['ASF', 'EDC', 'JPL', 'JPL-public'])
    parser.add_argument('-n', '--api-name', required=True)
    parser.add_argument('-c', '--cost-profile', required=True)
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
