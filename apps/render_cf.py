import argparse
import json
from pathlib import Path

import jinja2
import yaml


def snake_to_pascal_case(input_string: str):
    split_string = input_string.lower().split('_')
    return ''.join([i.title() for i in split_string])


def render_templates(job_types: dict, security_environment: str, api_name: str, server_urls: list[str]):
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
            server_urls=server_urls,
            json=json,
            snake_to_pascal_case=snake_to_pascal_case,
        )

        template_file.with_suffix('').write_text(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-j', '--job-spec-files', required=True, nargs='+', type=Path)
    parser.add_argument('-s', '--security-environment', default='ASF', choices=['ASF', 'EDC', 'JPL', 'JPL-public'])
    parser.add_argument('-n', '--api-name', required=True)
    parser.add_argument('-u', '--server-urls', required=True)
    args = parser.parse_args()

    server_urls = args.server_urls.split(',')

    job_types = {}
    for file in args.job_spec_files:
        job_types.update(yaml.safe_load(file.read_text()))

    for job_type, job_spec in job_types.items():
        for task in job_spec['tasks']:
            task['name'] = job_type + '_' + task['name'] if task['name'] else job_type

    render_templates(job_types, args.security_environment, args.api_name, server_urls)


if __name__ == '__main__':
    main()
