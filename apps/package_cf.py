from argparse import ArgumentParser
from pathlib import Path

import jinja2
import yaml


def render_template(template_file, job_types, env):
    output_file = template_file.with_suffix('')
    print(f'Rendering {template_file} to {output_file}')

    template = env.get_template(str(template_file))
    with open(output_file, 'w') as f:
        f.write(template.render(job_types=job_types))


def render_templates(job_types):
    env = get_env()
    for template_file in Path('.').glob('*.j2'):
        render_template(template_file, job_types, env)


def get_env():
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('./'),
        autoescape=jinja2.select_autoescape(),
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    return env


def main():
    parser = ArgumentParser()
    parser.add_argument('--job-types-file', required=True)
    job_types_file = parser.parse_args().job_types_file

    with open(job_types_file) as f:
        job_types = yaml.safe_load(f)

    render_templates(job_types)


if __name__ == '__main__':
    main()
