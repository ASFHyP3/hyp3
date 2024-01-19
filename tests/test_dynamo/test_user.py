import dynamo


# TODO update these field names?
def test_get_user(tables):
    table_items = [
        {
            'user_id': 'user1',
            'max_jobs_per_user': 5
        },
        {
            'user_id': 'user2',
            'max_jobs_per_user': 15
        },
    ]
    for item in table_items:
        tables.users_table.put_item(Item=item)

    assert dynamo.user.get_user('user1') == table_items[0]
    assert dynamo.user.get_user('user2') == table_items[1]
    assert dynamo.user.get_user('foo') is None
