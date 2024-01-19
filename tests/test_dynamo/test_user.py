import pytest

import dynamo


def test_get_user(tables):
    table_items = [
        {
            'user_id': 'user1',
            'remaining_credits': 5
        },
        {
            'user_id': 'user2',
            'remaining_credits': 15
        },
    ]
    for item in table_items:
        tables.users_table.put_item(Item=item)

    assert dynamo.user.get_user('user1') == table_items[0]
    assert dynamo.user.get_user('user2') == table_items[1]
    assert dynamo.user.get_user('foo') is None


def test_create_user(tables, monkeypatch):
    monkeypatch.setenv('DEFAULT_CREDITS_PER_USER', '25')

    user1 = dynamo.user.create_user('user1')
    assert user1 == {
        'user_id': 'user1',
        'remaining_credits': 25,
    }

    user2 = dynamo.user.create_user('user2')
    assert user2 == {
        'user_id': 'user2',
        'remaining_credits': 25,
    }

    response = tables.users_table.scan()
    assert response['Items'] == [user1, user2]

    with pytest.raises(ValueError):
        dynamo.user.create_user('user1')
