from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import process_new_granules


# TODO update
def test_lambda_handler(tables):
    assert False
    # items = [
    #     {
    #         'subscription_id': 'sub1',
    #         'creation_date': '2020-01-01T00:00:00+00:00',
    #         'job_type': 'INSAR_GAMMA',
    #         'search_parameters': {
    #             'start': datetime.now(tz=timezone.utc).isoformat(timespec='seconds'),
    #             'end': (datetime.now(tz=timezone.utc) + timedelta(days=5)).isoformat(timespec='seconds'),
    #         },
    #         'user_id': 'user1',
    #         'enabled': True,
    #     },
    #     {
    #         'subscription_id': 'sub2',
    #         'creation_date': '2020-01-01T00:00:00+00:00',
    #         'job_type': 'INSAR_GAMMA',
    #         'user_id': 'user1',
    #         'enabled': False
    #     },
    #     {
    #         'subscription_id': 'sub3',
    #         'creation_date': '2020-01-01T00:00:00+00:00',
    #         'job_type': 'INSAR_GAMMA',
    #         'search_parameters': {
    #             'start': (datetime.now(tz=timezone.utc) - timedelta(days=15)).isoformat(timespec='seconds'),
    #             'end': (datetime.now(tz=timezone.utc) - timedelta(days=5)).isoformat(timespec='seconds'),
    #         },
    #         'user_id': 'user1',
    #         'enabled': True,
    #     },
    #     {
    #         'subscription_id': 'sub4',
    #         'creation_date': '2020-01-01T00:00:00+00:00',
    #         'job_type': 'INSAR_GAMMA',
    #         'search_parameters': {
    #             'start': (datetime.now(tz=timezone.utc) - timedelta(days=15)).isoformat(timespec='seconds'),
    #             'end': (datetime.now(tz=timezone.utc) - timedelta(days=5)).isoformat(timespec='seconds'),
    #         },
    #         'user_id': 'user1',
    #         'enabled': True,
    #     },
    # ]
    # for item in items:
    #     tables.subscriptions_table.put_item(Item=item)
    #
    # def mock_get_unprocessed_granules(subscription):
    #     if subscription['subscription_id'] == 'sub4':
    #         return ['notempty']
    #     else:
    #         return []
    #
    # with patch('process_new_granules.handle_subscription') as p:
    #     with patch('process_new_granules.get_unprocessed_granules', mock_get_unprocessed_granules):
    #         process_new_granules.lambda_handler(1, 1)
    #         assert p.call_count == 3
    #
    # response = tables.subscriptions_table.scan()['Items']
    # sub3 = [sub for sub in response if sub['subscription_id'] == 'sub3'][0]
    # assert sub3['enabled'] is False
    #
    # sub4 = [sub for sub in response if sub['subscription_id'] == 'sub4'][0]
    # assert sub4['enabled'] is True
