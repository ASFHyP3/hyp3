import pprint
from pathlib import Path, PurePosixPath

import jinja2
import yaml
import json


def render_template(template_file, job_types, env):
    output_file = template_file.with_suffix('')
    print(f'Rendering {template_file} to {output_file}')

    template = env.get_template(str(template_file))
    with open(output_file, 'w') as f:
        f.write(template.render(job_types=job_types, json=json))


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
    job_types = {}
    job_spec_path = Path('./job_spec')
    for file in job_spec_path.glob('*.yml'):
        with open(file.absolute()) as f:
            job_types[file.stem] = yaml.safe_load(f)
    # pprint.pprint(job_types)
    render_templates(job_types)

if __name__ == '__main__':
    main()
