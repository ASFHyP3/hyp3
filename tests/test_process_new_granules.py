from os import environ

import pytest
from moto import mock_dynamodb2

from process_new_granuels import DB


@pytest.fixture
def tables(table_properties):
    with mock_dynamodb2():
        class Tables:
            jobs_table = DB.create_table(
                TableName=environ['JOBS_TABLE_NAME'],
                **table_properties.jobs_table,
            )
            users_table = DB.create_table(
                TableName=environ['USERS_TABLE_NAME'],
                **table_properties.users_table,
            )
            subscriptions_table = DB.create_table(
                TableName=environ['SUBSCRIPTIONS_TABLE_NAME'],
                **table_properties.subscriptions_table
            )

        tables = Tables()
        yield tables
