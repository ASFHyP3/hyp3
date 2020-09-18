from argparse import ArgumentParser

import jinja2
import yaml


def main():
    parser = ArgumentParser()
    parser.add_argument('--job-types', required=True)
    job_types_file = parser.parse_args().job_types

    with open(job_types_file) as f:
        job_types = yaml.safe_load(f)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('./'),
        autoescape=jinja2.select_autoescape(),
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        )
    workflow_cf = env.get_template('workflow-cf.j2.yml')
    stepfunction = env.get_template('step-function.j2.json')
    with open('step-function.json', 'w') as f:
        f.write(stepfunction.render(job_types=job_types))
    with open('workflow-cf.yml', 'w') as f:
        f.write(workflow_cf.render(job_types=job_types))


if __name__ == '__main__':
    main()
