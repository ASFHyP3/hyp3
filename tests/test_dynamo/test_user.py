import dynamo


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


def test_get_max_jobs_per_month(tables, monkeypatch):
    monkeypatch.setenv('MONTHLY_JOB_QUOTA_PER_USER', '5')
    assert dynamo.user.get_max_jobs_per_month('user1') == 5

    user = {'user_id': 'user1'}
    tables.users_table.put_item(Item=user)
    assert dynamo.user.get_max_jobs_per_month('user1') == 5

    user['max_jobs_per_month'] = 10
    tables.users_table.put_item(Item=user)
    assert dynamo.user.get_max_jobs_per_month('user1') == 10

    user['max_jobs_per_month'] = None
    tables.users_table.put_item(Item=user)
    assert dynamo.user.get_max_jobs_per_month('user1') is None


def test_get_priority(tables):
    assert dynamo.user.get_priority('user1') is None

    user = {'user_id': 'user1'}
    tables.users_table.put_item(Item=user)
    assert dynamo.user.get_priority('user1') is None

    user['priority'] = 10
    tables.users_table.put_item(Item=user)
    assert dynamo.user.get_priority('user1') == 10
