import argparse
import json
from pathlib import Path, PurePosixPath

import jinja2
import yaml


def snake_to_pascal_case(input_string: str):
    split_string = input_string.lower().split('_')
    return ''.join([i.title() for i in split_string])


def render_template(template_file, job_types, env):
    output_file = template_file.with_suffix('')

    template = env.get_template(str(template_file))
    with open(output_file, 'w') as f:
        f.write(template.render(job_types=job_types, json=json, snake_to_pascal_case=snake_to_pascal_case))


def render_templates(job_types):
    env = get_env()
    for template_file in Path('.').glob('**/*.j2'):
        render_template(PurePosixPath(template_file), job_types, env)


def get_env():
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('./'),
        autoescape=jinja2.select_autoescape(default=True, disabled_extensions=('j2',)),
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    return env


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='+', type=Path)
    args = parser.parse_args()

    job_types = {}
    for file in args.paths:
        with open(file.absolute()) as f:
            job_types.update(yaml.safe_load(f))
    render_templates(job_types)


if __name__ == '__main__':
    main()
