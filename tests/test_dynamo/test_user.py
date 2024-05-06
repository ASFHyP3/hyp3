import unittest.mock
from decimal import Decimal

import botocore.exceptions
import pytest

import dynamo.user
from dynamo.user import APPLICATION_APPROVED, APPLICATION_NOT_STARTED


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


def test_get_or_create_user_create(tables):
    with unittest.mock.patch('dynamo.user._create_user') as mock_create_user:
        mock_create_user.return_value = 'create_user_return_value'

        user = dynamo.user.get_or_create_user('foo')

        mock_create_user.assert_called_once_with(
            user_id='foo',
            users_table=tables.users_table,
        )

    assert user == 'create_user_return_value'


def test_create_user(tables):
    user = dynamo.user._create_user(user_id='foo', users_table=tables.users_table)

    assert user == {
        'user_id': 'foo', 'remaining_credits': Decimal(0), 'application_status': APPLICATION_NOT_STARTED
    }
    assert tables.users_table.scan()['Items'] == [user]


def test_create_user_already_exists(tables):
    tables.users_table.put_item(Item={'user_id': 'foo'})

    with pytest.raises(dynamo.user.DatabaseConditionException):
        dynamo.user._create_user(user_id='foo', users_table=tables.users_table)

    assert tables.users_table.scan()['Items'] == [{'user_id': 'foo'}]


def test_reset_credits(tables, monkeypatch):
    original_user_record = {
        'user_id': 'foo',
        'remaining_credits': Decimal(10),
        'application_status': APPLICATION_APPROVED,
    }
    tables.users_table.put_item(Item=original_user_record)

    user = dynamo.user._reset_credits_if_needed(
        user=original_user_record,
        default_credits=Decimal(25),
        current_month='2024-02',
        users_table=tables.users_table,
    )

    assert user == {
        'user_id': 'foo',
        'remaining_credits': Decimal(25),
        '_month_of_last_credit_reset': '2024-02',
        'application_status': APPLICATION_APPROVED,
    }
    assert tables.users_table.scan()['Items'] == [user]


def test_reset_credits_month_exists(tables, monkeypatch):
    original_user_record = {
        'user_id': 'foo',
        'remaining_credits': Decimal(10),
        '_month_of_last_credit_reset': '2024-01',
        'application_status': APPLICATION_APPROVED,
    }
    tables.users_table.put_item(Item=original_user_record)

    user = dynamo.user._reset_credits_if_needed(
        user=original_user_record,
        default_credits=Decimal(25),
        current_month='2024-02',
        users_table=tables.users_table,
    )

    assert user == {
        'user_id': 'foo',
        'remaining_credits': Decimal(25),
        '_month_of_last_credit_reset': '2024-02',
        'application_status': APPLICATION_APPROVED,
    }
    assert tables.users_table.scan()['Items'] == [user]


def test_reset_credits_override(tables, monkeypatch):
    original_user_record = {
        'user_id': 'foo',
        'remaining_credits': Decimal(10),
        'credits_per_month': Decimal(50),
        'application_status': APPLICATION_APPROVED,
    }
    tables.users_table.put_item(Item=original_user_record)

    user = dynamo.user._reset_credits_if_needed(
        user=original_user_record,
        default_credits=Decimal(25),
        current_month='2024-02',
        users_table=tables.users_table,
    )

    assert user == {
        'user_id': 'foo',
        'remaining_credits': Decimal(50),
        'credits_per_month': Decimal(50),
        '_month_of_last_credit_reset': '2024-02',
        'application_status': APPLICATION_APPROVED,
    }
    assert tables.users_table.scan()['Items'] == [user]


def test_reset_credits_same_month(tables, monkeypatch):
    original_user_record = {
        'user_id': 'foo',
        'remaining_credits': Decimal(10),
        '_month_of_last_credit_reset': '2024-02',
        'application_status': APPLICATION_APPROVED,
    }
    tables.users_table.put_item(Item=original_user_record)

    user = dynamo.user._reset_credits_if_needed(
        user=original_user_record,
        default_credits=Decimal(25),
        current_month='2024-02',
        users_table=tables.users_table,
    )

    assert user == {
        'user_id': 'foo',
        'remaining_credits': Decimal(10),
        '_month_of_last_credit_reset': '2024-02',
        'application_status': APPLICATION_APPROVED,
    }
    assert tables.users_table.scan()['Items'] == [user]


def test_reset_credits_infinite_credits(tables, monkeypatch):
    original_user_record = {
        'user_id': 'foo',
        'remaining_credits': None,
        'application_status': APPLICATION_APPROVED,
    }
    tables.users_table.put_item(Item=original_user_record)

    user = dynamo.user._reset_credits_if_needed(
        user=original_user_record,
        default_credits=Decimal(25),
        current_month='2024-02',
        users_table=tables.users_table,
    )

    assert user == {
        'user_id': 'foo',
        'remaining_credits': None,
        'application_status': APPLICATION_APPROVED,
    }
    assert tables.users_table.scan()['Items'] == [user]


def test_reset_credits_to_zero(tables):
    original_user_record = {
        'user_id': 'foo',
        'remaining_credits': Decimal(10),
        '_month_of_last_credit_reset': '2024-02',
        'application_status': 'bar',
    }
    tables.users_table.put_item(Item=original_user_record)

    user = dynamo.user._reset_credits_if_needed(
        user=original_user_record,
        default_credits=Decimal(25),
        current_month='2024-02',
        users_table=tables.users_table,
    )

    assert user == {
        'user_id': 'foo',
        'remaining_credits': Decimal(0),
        'application_status': 'bar',
    }
    assert tables.users_table.scan()['Items'] == [user]


def test_reset_credits_already_at_zero(tables):
    original_user_record = {
        'user_id': 'foo',
        'remaining_credits': Decimal(0),
        '_month_of_last_credit_reset': '2024-02',
        'application_status': 'bar',
    }
    tables.users_table.put_item(Item=original_user_record)

    user = dynamo.user._reset_credits_if_needed(
        user=original_user_record,
        default_credits=Decimal(25),
        current_month='2024-02',
        users_table=tables.users_table,
    )

    assert user == {
        'user_id': 'foo',
        'remaining_credits': Decimal(0),
        '_month_of_last_credit_reset': '2024-02',
        'application_status': 'bar',
    }
    assert tables.users_table.scan()['Items'] == [user]


def test_reset_credits_failed_not_approved(tables):
    tables.users_table.put_item(
        Item={
            'user_id': 'foo',
            'remaining_credits': Decimal(10),
            'application_status': 'bar',
        }
    )

    with pytest.raises(dynamo.user.DatabaseConditionException):
        dynamo.user._reset_credits_if_needed(
            user={
                'user_id': 'foo',
                'remaining_credits': Decimal(10),
                'application_status': APPLICATION_APPROVED,
            },
            default_credits=Decimal(25),
            current_month='2024-02',
            users_table=tables.users_table,
        )

    assert tables.users_table.scan()['Items'] == [{
        'user_id': 'foo',
        'remaining_credits': Decimal(10),
        'application_status': 'bar',
    }]


def test_reset_credits_failed_same_month(tables, monkeypatch):
    tables.users_table.put_item(
        Item={
            'user_id': 'foo',
            'remaining_credits': Decimal(10),
            '_month_of_last_credit_reset': '2024-02',
            'application_status': APPLICATION_APPROVED,
        }
    )

    with pytest.raises(dynamo.user.DatabaseConditionException):
        dynamo.user._reset_credits_if_needed(
            user={
                'user_id': 'foo',
                'remaining_credits': Decimal(10),
                '_month_of_last_credit_reset': '2024-01',
                'application_status': APPLICATION_APPROVED,
            },
            default_credits=Decimal(25),
            current_month='2024-02',
            users_table=tables.users_table,
        )

    assert tables.users_table.scan()['Items'] == [{
        'user_id': 'foo',
        'remaining_credits': Decimal(10),
        '_month_of_last_credit_reset': '2024-02',
        'application_status': APPLICATION_APPROVED,
    }]


def test_reset_credits_failed_infinite_credits(tables, monkeypatch):
    tables.users_table.put_item(
        Item={
            'user_id': 'foo',
            'remaining_credits': None,
            'application_status': APPLICATION_APPROVED,
        }
    )

    with pytest.raises(dynamo.user.DatabaseConditionException):
        dynamo.user._reset_credits_if_needed(
            user={
                'user_id': 'foo',
                'remaining_credits': Decimal(10),
                'application_status': APPLICATION_APPROVED,
            },
            default_credits=Decimal(25),
            current_month='2024-02',
            users_table=tables.users_table,
        )

    assert tables.users_table.scan()['Items'] == [{
        'user_id': 'foo',
        'remaining_credits': None,
        'application_status': APPLICATION_APPROVED,
    }]


def test_reset_credits_failed_approved(tables):
    tables.users_table.put_item(
        Item={
            'user_id': 'foo',
            'remaining_credits': Decimal(10),
            '_month_of_last_credit_reset': '2024-02',
            'application_status': APPLICATION_APPROVED,
        }
    )

    with pytest.raises(dynamo.user.DatabaseConditionException):
        dynamo.user._reset_credits_if_needed(
            user={
                'user_id': 'foo',
                'remaining_credits': Decimal(10),
                '_month_of_last_credit_reset': '2024-02',
                'application_status': 'bar',
            },
            default_credits=Decimal(25),
            current_month='2024-02',
            users_table=tables.users_table,
        )

    assert tables.users_table.scan()['Items'] == [{
        'user_id': 'foo',
        'remaining_credits': Decimal(10),
        '_month_of_last_credit_reset': '2024-02',
        'application_status': APPLICATION_APPROVED,
    }]


def test_reset_credits_failed_zero_credits(tables):
    tables.users_table.put_item(
        Item={
            'user_id': 'foo',
            'remaining_credits': Decimal(0),
            '_month_of_last_credit_reset': '2024-02',
            'application_status': 'bar',
        }
    )

    with pytest.raises(dynamo.user.DatabaseConditionException):
        dynamo.user._reset_credits_if_needed(
            user={
                'user_id': 'foo',
                'remaining_credits': Decimal(10),
                '_month_of_last_credit_reset': '2024-02',
                'application_status': 'bar',
            },
            default_credits=Decimal(25),
            current_month='2024-02',
            users_table=tables.users_table,
        )

    assert tables.users_table.scan()['Items'] == [{
        'user_id': 'foo',
        'remaining_credits': Decimal(0),
        '_month_of_last_credit_reset': '2024-02',
        'application_status': 'bar',
    }]


def test_decrement_credits(tables):
    tables.users_table.put_item(Item={'user_id': 'foo', 'remaining_credits': Decimal(25)})

    dynamo.user.decrement_credits('foo', 1)
    assert tables.users_table.scan()['Items'] == [{'user_id': 'foo', 'remaining_credits': Decimal(24)}]

    dynamo.user.decrement_credits('foo', 4)
    assert tables.users_table.scan()['Items'] == [{'user_id': 'foo', 'remaining_credits': Decimal(20)}]

    dynamo.user.decrement_credits('foo', 20)
    assert tables.users_table.scan()['Items'] == [{'user_id': 'foo', 'remaining_credits': Decimal(0)}]


def test_decrement_credits_invalid_cost(tables):
    with pytest.raises(ValueError, match=r'^Cost 0 <= 0$'):
        dynamo.user.decrement_credits('foo', 0)

    assert tables.users_table.scan()['Items'] == []

    with pytest.raises(ValueError, match=r'^Cost -1 <= 0$'):
        dynamo.user.decrement_credits('foo', -1)

    assert tables.users_table.scan()['Items'] == []


def test_decrement_credits_cost_too_high(tables):
    tables.users_table.put_item(Item={'user_id': 'foo', 'remaining_credits': Decimal(1)})

    with pytest.raises(dynamo.user.DatabaseConditionException):
        dynamo.user.decrement_credits('foo', 2)

    assert tables.users_table.scan()['Items'] == [{'user_id': 'foo', 'remaining_credits': Decimal(1)}]

    dynamo.user.decrement_credits('foo', 1)

    assert tables.users_table.scan()['Items'] == [{'user_id': 'foo', 'remaining_credits': Decimal(0)}]

    with pytest.raises(dynamo.user.DatabaseConditionException):
        dynamo.user.decrement_credits('foo', 1)

    assert tables.users_table.scan()['Items'] == [{'user_id': 'foo', 'remaining_credits': Decimal(0)}]


def test_decrement_credits_infinite_credits(tables):
    tables.users_table.put_item(Item={'user_id': 'foo', 'remaining_credits': None})

    with pytest.raises(
            botocore.exceptions.ClientError,
            match=r'^An error occurred \(ValidationException\) when calling the UpdateItem operation:'
                  r' An operand in the update expression has an incorrect data type$'
    ):
        dynamo.user.decrement_credits('foo', 1)

    assert tables.users_table.scan()['Items'] == [{'user_id': 'foo', 'remaining_credits': None}]


def test_decrement_credits_user_does_not_exist(tables):
    with pytest.raises(dynamo.user.DatabaseConditionException):
        dynamo.user.decrement_credits('foo', 1)

    assert tables.users_table.scan()['Items'] == []
