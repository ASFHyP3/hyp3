import unittest.mock
from decimal import Decimal

import pytest

import dynamo.user


def test_get_or_create_user_reset(tables, monkeypatch):
    monkeypatch.setenv('DEFAULT_CREDITS_PER_USER', '25')
    monkeypatch.setenv('RESET_CREDITS_MONTHLY', 'yes')
    tables.users_table.put_item(
        Item={'user_id': 'foo', 'remaining_credits': Decimal(10), 'month_of_last_credits_reset': '2024-01'}
    )

    with unittest.mock.patch('dynamo.user._get_current_month') as mock_get_current_month:
        mock_get_current_month.return_value = '2024-02'
        user = dynamo.user.get_or_create_user('foo')

    assert user == {'user_id': 'foo', 'remaining_credits': Decimal(25), 'month_of_last_credits_reset': '2024-02'}
    assert user == tables.users_table.get_item(Key={'user_id': 'foo'})['Item']


def test_get_or_create_user_no_reset(tables, monkeypatch):
    monkeypatch.setenv('DEFAULT_CREDITS_PER_USER', '25')
    monkeypatch.setenv('RESET_CREDITS_MONTHLY', 'no')
    tables.users_table.put_item(
        Item={'user_id': 'foo', 'remaining_credits': Decimal(10), 'month_of_last_credits_reset': '2024-01'}
    )

    with unittest.mock.patch('dynamo.user._get_current_month') as mock_get_current_month:
        mock_get_current_month.return_value = '2024-02'
        user = dynamo.user.get_or_create_user('foo')

    assert user == {'user_id': 'foo', 'remaining_credits': Decimal(10), 'month_of_last_credits_reset': '2024-01'}
    assert user == tables.users_table.get_item(Key={'user_id': 'foo'})['Item']


def test_get_or_create_user_create(tables, monkeypatch):
    monkeypatch.setenv('DEFAULT_CREDITS_PER_USER', '25')

    with unittest.mock.patch('dynamo.user._get_current_month') as mock_get_current_month:
        mock_get_current_month.return_value = '2024-02'
        user = dynamo.user.get_or_create_user('foo')

    assert user == {'user_id': 'foo', 'remaining_credits': Decimal(25), 'month_of_last_credits_reset': '2024-02'}
    assert user == tables.users_table.get_item(Key={'user_id': 'foo'})['Item']


# TODO update
def test_decrement_credits(tables):
    with pytest.raises(ValueError):
        dynamo.user.decrement_credits('foo', 1)

    user = {'user_id': 'foo', 'remaining_credits': 25}
    tables.users_table.put_item(Item=user)

    with pytest.raises(ValueError):
        dynamo.user.decrement_credits('foo', -1)

    dynamo.user.decrement_credits('foo', 1)
    response = tables.users_table.scan()
    assert response['Items'] == [{'user_id': 'foo', 'remaining_credits': 24}]

    dynamo.user.decrement_credits('foo', 4)
    response = tables.users_table.scan()
    assert response['Items'] == [{'user_id': 'foo', 'remaining_credits': 20}]

    # TODO should this case set remaining_credits to zero?
    with pytest.raises(ValueError):
        dynamo.user.decrement_credits('foo', 21)
    response = tables.users_table.scan()
    assert response['Items'] == [{'user_id': 'foo', 'remaining_credits': 20}]

    dynamo.user.decrement_credits('foo', 20)
    response = tables.users_table.scan()
    assert response['Items'] == [{'user_id': 'foo', 'remaining_credits': 0}]
