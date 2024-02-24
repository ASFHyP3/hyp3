import unittest.mock
from decimal import Decimal
from http import HTTPStatus

from test_api.conftest import COSTS_URI


# FIXME fails with 403
def test_get_costs(client):
    costs = {'foo': Decimal('1.3')}
    with unittest.mock.patch('dynamo.jobs.COSTS', costs):
        response = client.get(COSTS_URI)

    assert response.status_code == HTTPStatus.OK
    assert response.json == {'foo': 1.3}
