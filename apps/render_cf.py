import argparse
import json
from pathlib import Path

import jinja2
import yaml


def snake_to_pascal_case(input_string: str):
    split_string = input_string.lower().split('_')
    return ''.join([i.title() for i in split_string])


def render_templates(job_types, security_environment, api_name, secrets):
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
            secrets=secrets,
            json=json,
            snake_to_pascal_case=snake_to_pascal_case,
        )

        template_file.with_suffix('').write_text(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-j', '--job-spec-files', required=True, nargs='+', type=Path)
    parser.add_argument('-s', '--security-environment', default='ASF', choices=['ASF', 'EDC', 'JPL', 'JPL-public'])
    parser.add_argument('-n', '--api-name', required=True)
    args = parser.parse_args()

    job_types = {}
    for file in args.job_spec_files:
        job_types.update(yaml.safe_load(file.read_text()))

    required_secrets = []
    for job_type, job_spec in job_types.items():
        for task in job_spec['tasks']:
            task['name'] = job_type + '_' + task['name'] if task['name'] else job_type
            if secrets := task.get('secrets'):
                for secret in secrets:
                    required_secrets.append({
                        'env_var': secret,
                        'secret_name': secret.lower(),
                        'cf_parameter_name': secret.title()
                    })

    # ensure no repeated secrets
    required_secrets = [dict(s) for s in set(frozenset(d.items()) for d in required_secrets)]

    render_templates(job_types, args.security_environment, args.api_name, required_secrets)


if __name__ == '__main__':
    main()
