from decimal import Decimal
from os import environ, path

import pytest
import yaml
from moto import mock_aws

from dynamo.user import APPLICATION_APPROVED


@pytest.fixture
def table_properties():
    class TableProperties:
        jobs_table = get_table_properties_from_template('JobsTable')
        users_table = get_table_properties_from_template('UsersTable')
        access_codes_table = get_table_properties_from_template('AccessCodesTable')
    return TableProperties()


def get_table_properties_from_template(resource_name):
    yaml.SafeLoader.add_multi_constructor('!', lambda loader, suffix, node: None)
    template_file = path.join(path.dirname(__file__), '../apps/main-cf.yml')
    with open(template_file, 'r') as f:
        template = yaml.safe_load(f)
    table_properties = template['Resources'][resource_name]['Properties']
    return table_properties


@mock_aws
@pytest.fixture
def tables(table_properties):
    with mock_aws():
        from dynamo import DYNAMODB_RESOURCE

        class Tables:
            jobs_table = DYNAMODB_RESOURCE.create_table(
                TableName=environ['JOBS_TABLE_NAME'],
                **table_properties.jobs_table,
            )
            users_table = DYNAMODB_RESOURCE.create_table(
                TableName=environ['USERS_TABLE_NAME'],
                **table_properties.users_table,
            )
            access_codes_table = DYNAMODB_RESOURCE.create_table(
                TableName=environ['ACCESS_CODES_TABLE_NAME'],
                **table_properties.access_codes_table,
            )
        tables = Tables()
        yield tables


@pytest.fixture
def approved_user(tables) -> str:
    user = {
        'user_id': 'approved_user',
        'remaining_credits': Decimal(0),
        'application_status': APPLICATION_APPROVED,
    }
    tables.users_table.put_item(Item=user)
    return user['user_id']


def list_have_same_elements(l1, l2):
    return [item for item in l1 if item not in l2] == [] == [item for item in l2 if item not in l1]
