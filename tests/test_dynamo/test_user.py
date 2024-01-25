import pytest

import dynamo.user


# TODO update?
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
