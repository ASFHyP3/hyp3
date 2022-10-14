import os
from unittest.mock import call, patch

import subscription_manager

TEST_WORKER_ARN = 'test-worker-arn'


def test_lambda_handler(tables):
    items = [
        {'subscription_id': 'sub1', 'enabled': True},
        {'subscription_id': 'sub2', 'enabled': False},
        {'subscription_id': 'sub3', 'enabled': True},
        {'subscription_id': 'sub4', 'enabled': True},
    ]
    for item in items:
        tables.subscriptions_table.put_item(Item=item)

    with patch('subscription_manager.invoke_worker') as mock_invoke_worker, \
            patch.dict(os.environ, {'SUBSCRIPTION_WORKER_ARN': TEST_WORKER_ARN}, clear=True):
        mock_invoke_worker.return_value = {'StatusCode': None}

        subscription_manager.lambda_handler(None, None)

        assert mock_invoke_worker.mock_calls == [
            call(TEST_WORKER_ARN, items[0]),
            call(TEST_WORKER_ARN, items[2]),
            call(TEST_WORKER_ARN, items[3]),
        ]
