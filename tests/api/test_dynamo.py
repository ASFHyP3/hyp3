from hyp3_api import dynamo


def test_query_jobs_by_user(tables):
    table_items = [
        {
            'job_id': 'job1',
            'user_id': 'user1',
            'job_type': 'fake job type',
            'status_code': 'fake job stats',
            'request_time': '2000-10-01T00:00:00+00:00'
        },
        {
            'job_id': 'job2',
            'user_id': 'user1',
            'job_type': 'fake job type',
            'status_code': 'fake job stats',
            'request_time': '2000-01-01T00:00:00+00:00'
        },
        {
            'job_id': 'job3',
            'user_id': 'user2',
            'job_type': 'fake job type',
            'status_code': 'fake job stats',
            'request_time': '2000-01-01T00:00:00+00:00'
        },
    ]
    for item in table_items:
        tables['jobs_table'].put_item(Item=item)

    response = dynamo.query_jobs('user1')
    assert len(response) == 2
    assert [i for i in response if i not in table_items[:2]] == []


def test_query_jobs_by_time(tables):
    table_items = [
        {
            'job_id': 'job1',
            'user_id': 'user1',
            'job_type': 'fake job type',
            'status_code': 'fake job stats',
            'request_time': '2000-01-01T00:00:00+00:00'
        },
        {
            'job_id': 'job2',
            'user_id': 'user1',
            'job_type': 'fake job type',
            'status_code': 'fake job stats',
            'request_time': '2000-01-02T00:00:00+00:00'
        },
        {
            'job_id': 'job3',
            'user_id': 'user1',
            'job_type': 'fake job type',
            'status_code': 'fake job stats',
            'request_time': '2000-01-03T00:00:00+00:00'
        },
    ]
    for item in table_items:
        tables['jobs_table'].put_item(Item=item)

    start = '2000-01-01T00:00:00z'
    end = '2000-01-03T00:00:00z'
    response = dynamo.query_jobs('user1', start, end)
    assert len(response) == 3
    assert response == table_items

    start = '2000-01-01T00:00:01z'
    end = '2000-01-02T00:59:59z'
    response = dynamo.query_jobs('user1', start, end)
    assert len(response) == 1
    assert [i for i in response if i not in table_items[1:2]] == []


def test_query_jobs_by_status(tables):
    table_items = [
        {
            'job_id': 'job1',
            'user_id': 'user1',
            'job_type': 'fake job type',
            'status_code': 'status1',
            'request_time': '2000-10-01T00:00:00+00:00'
        },
        {
            'job_id': 'job2',
            'user_id': 'user1',
            'job_type': 'fake job type',
            'status_code': 'status2',
            'request_time': '2000-01-01T00:00:00+00:00'
        },
        {
            'job_id': 'job3',
            'user_id': 'user1',
            'job_type': 'fake job type',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00'
        },
    ]
    for item in table_items:
        tables['jobs_table'].put_item(Item=item)

    response = dynamo.query_jobs('user1', status_code='status1')
    assert len(response) == 2
    assert [i for i in response if i not in table_items[0::2]] == []


def test_query_jobs_by_name(tables):
    table_items = [
        {
            'job_id': 'job1',
            'name': 'name1',
            'user_id': 'user1',
            'job_type': 'fake job type',
            'status_code': 'status1',
            'request_time': '2000-10-01T00:00:00+00:00'
        },
        {
            'job_id': 'job2',
            'name': 'name1',
            'user_id': 'user1',
            'job_type': 'fake job type',
            'status_code': 'status2',
            'request_time': '2000-01-01T00:00:00+00:00'
        },
        {
            'job_id': 'job3',
            'name': 'name2',
            'user_id': 'user1',
            'job_type': 'fake job type',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00'
        },
    ]
    for item in table_items:
        tables['jobs_table'].put_item(Item=item)

    response = dynamo.query_jobs('user1', name='name1')
    assert len(response) == 2
    assert [i for i in response if i not in table_items[:2]] == []


def test_put_jobs(tables):
    table_items = [
        {
            'job_id': 'job1',
            'name': 'name1',
            'user_id': 'user1',
            'job_type': 'fake job type',
            'status_code': 'status1',
            'request_time': '2000-10-01T00:00:00+00:00'
        },
        {
            'job_id': 'job2',
            'name': 'name1',
            'user_id': 'user1',
            'job_type': 'fake job type',
            'status_code': 'status2',
            'request_time': '2000-01-01T00:00:00+00:00'
        },
        {
            'job_id': 'job3',
            'name': 'name2',
            'user_id': 'user2',
            'job_type': 'fake job type',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00'
        },
    ]
    dynamo.put_jobs(table_items)
    response = tables['jobs_table'].scan()
    assert response['Items'] == table_items


def test_get_job(tables):
    table_items = [
        {
            'job_id': 'job1',
            'name': 'name1',
            'user_id': 'user1',
            'job_type': 'fake job type',
            'status_code': 'status1',
            'request_time': '2000-10-01T00:00:00+00:00'
        },
        {
            'job_id': 'job2',
            'name': 'name1',
            'user_id': 'user1',
            'job_type': 'fake job type',
            'status_code': 'status2',
            'request_time': '2000-01-01T00:00:00+00:00'
        },
        {
            'job_id': 'job3',
            'name': 'name2',
            'user_id': 'user1',
            'job_type': 'fake job type',
            'status_code': 'status1',
            'request_time': '2000-01-01T00:00:00+00:00'
        },
    ]
    for item in table_items:
        tables['jobs_table'].put_item(Item=item)

    assert dynamo.get_job('job1') == table_items[0]
    assert dynamo.get_job('job2') == table_items[1]
    assert dynamo.get_job('job3') == table_items[2]


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
        tables['users_table'].put_item(Item=item)

    assert dynamo.get_user('user1') == table_items[0]
    assert dynamo.get_user('user2') == table_items[1]
