import unittest.mock
from decimal import Decimal

import pytest

import dynamo.user


def test_get_or_create_user_reset(tables, monkeypatch):
    monkeypatch.setenv('DEFAULT_CREDITS_PER_USER', '25')
    tables.users_table.put_item(Item={'user_id': 'foo'})

    with unittest.mock.patch('dynamo.user._get_current_month') as mock_get_current_month, \
            unittest.mock.patch('dynamo.user._reset_credits_if_needed') as mock_reset_credits_if_needed:
        mock_get_current_month.return_value = '2024-02'
        mock_reset_credits_if_needed.return_value = 'reset_credits_return_value'

        user = dynamo.user.get_or_create_user('foo')

        mock_get_current_month.assert_called_once_with()
        mock_reset_credits_if_needed.assert_called_once_with(
            user={'user_id': 'foo'},
            default_credits=Decimal(25),
            current_month='2024-02',
            users_table=tables.users_table,
        )

    assert user == 'reset_credits_return_value'


def test_get_or_create_user_create(tables, monkeypatch):
    monkeypatch.setenv('DEFAULT_CREDITS_PER_USER', '25')

    with unittest.mock.patch('dynamo.user._get_current_month') as mock_get_current_month, \
            unittest.mock.patch('dynamo.user._create_user') as mock_create_user:
        mock_get_current_month.return_value = '2024-02'
        mock_create_user.return_value = 'create_user_return_value'

        user = dynamo.user.get_or_create_user('foo')

        mock_get_current_month.assert_called_once_with()
        mock_create_user.assert_called_once_with(
            user_id='foo',
            default_credits=Decimal(25),
            current_month='2024-02',
            users_table=tables.users_table,
        )

    assert user == 'create_user_return_value'


def test_create_user(tables):
    user = dynamo.user._create_user(
        user_id='foo',
        default_credits=Decimal(25),
        current_month='2024-02',
        users_table=tables.users_table
    )

    assert user == {'user_id': 'foo', 'remaining_credits': Decimal(25), 'month_of_last_credits_reset': '2024-02'}
    assert user == tables.users_table.get_item(Key={'user_id': 'foo'})['Item']


def test_create_user_failed(tables):
    tables.users_table.put_item(Item={'user_id': 'foo'})

    with pytest.raises(dynamo.user.DatabaseConditionException):
        dynamo.user._create_user(
            user_id='foo',
            default_credits=Decimal(25),
            current_month='2024-02',
            users_table=tables.users_table
        )


def test_reset_credits(tables, monkeypatch):
    monkeypatch.setenv('RESET_CREDITS_MONTHLY', 'yes')

    original_user_record = {
        'user_id': 'foo', 'remaining_credits': Decimal(10), 'month_of_last_credits_reset': '2024-01'
    }
    tables.users_table.put_item(Item=original_user_record)

    user = dynamo.user._reset_credits_if_needed(
        user=original_user_record,
        default_credits=Decimal(25),
        current_month='2024-02',
        users_table=tables.users_table,
    )

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
