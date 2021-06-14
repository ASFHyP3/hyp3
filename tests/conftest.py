from os import path

import pytest
import yaml


@pytest.fixture
def table_properties():
    jobs_table = get_table_properties_from_template('JobsTable')
    users_table = get_table_properties_from_template('UsersTable')
    return {'JobsTable': jobs_table, 'UsersTable': users_table}


def get_table_properties_from_template(resource_name):
    yaml.SafeLoader.add_multi_constructor('!', lambda loader, suffix, node: None)
    template_file = path.join(path.dirname(__file__), '../apps/main-cf.yml')
    with open(template_file, 'r') as f:
        template = yaml.safe_load(f)
    table_properties = template['Resources'][resource_name]['Properties']
    return table_properties
