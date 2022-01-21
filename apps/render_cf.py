import argparse
import json
from pathlib import Path

import jinja2
import yaml


def snake_to_pascal_case(input_string: str):
    split_string = input_string.lower().split('_')
    return ''.join([i.title() for i in split_string])


def render_templates(job_types, security_environment):
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
            json=json,
            snake_to_pascal_case=snake_to_pascal_case
        )

        template_file.with_suffix('').write_text(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('job_spec', nargs='+', type=Path)
    parser.add_argument('-s', '--security-environment', default='ASF', choices=['ASF', 'EDC', 'JPL'])
    args = parser.parse_args()

    job_types = {}
    for file in args.job_spec:
        job_types.update(yaml.safe_load(file.read_text()))
    render_templates(job_types, args.security_environment)


if __name__ == '__main__':
    main()
