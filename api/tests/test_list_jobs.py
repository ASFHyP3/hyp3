from conftest import JOBS_URI, login, make_db_record
from flask_api import status


def test_list_jobs(client, table):
    files = [
        {
            'filename': 'foo.txt',
            'size': 123,
            'url': 'https://mybucket.s3.us-west-2.amazonaws.com/prefix/foo.txt',
        },
        {
            'filename': 'bar.png',
            'size': 0,
            'url': 'https://mybucket.s3.us-west-2.amazonaws.com/prefix/bar.png',
        },
    ]
    items = [
        make_db_record('0ddaeb98-7636-494d-9496-03ea4a7df266', user_id='user_with_jobs'),
        make_db_record('27836b79-e5b2-4d8f-932f-659724ea02c3', user_id='user_with_jobs', files=files)
    ]
    for item in items:
        table.put_item(Item=item)

    login(client, 'user_with_jobs')
    response = client.get(JOBS_URI)
    assert response.status_code == status.HTTP_200_OK
    assert response.json == {
        'jobs': items,
    }

    login(client, 'user_without_jobs')
    response = client.get(JOBS_URI)
    assert response.status_code == status.HTTP_200_OK
    assert response.json == {
        'jobs': [],
    }


def test_list_jobs_not_authorized(client, table):
    login(client, authorized=False)
    response = client.get(JOBS_URI)
    assert response.status_code == status.HTTP_200_OK
    assert response.json == {'jobs': []}


def test_list_jobs_by_status(client, table):
    items = [
        make_db_record('0ddaeb98-7636-494d-9496-03ea4a7df266', status_code='RUNNING'),
        make_db_record('27836b79-e5b2-4d8f-932f-659724ea02c3', status_code='SUCCEEDED')
    ]
    for item in items:
        table.put_item(Item=item)

    login(client)
    response = client.get(JOBS_URI, query_string={'status_code': 'RUNNING'})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json['jobs']) == 1
    assert response.json['jobs'][0] == items[0]

    response = client.get(JOBS_URI, query_string={'status_code': 'FAILED'})
    assert response.status_code == status.HTTP_200_OK
    assert response.json == {'jobs': []}


def test_list_jobs_bad_status(client):
    login(client)

    response = client.get(JOBS_URI, query_string={'status_code': 'BAD'})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.get(JOBS_URI, query_string={'status_code': ''})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_list_jobs_by_start(client, table):
    items = [
        make_db_record('0ddaeb98-7636-494d-9496-03ea4a7df266', request_time='2019-12-31T15:00:00Z'),
        make_db_record('27836b79-e5b2-4d8f-932f-659724ea02c3', request_time='2019-12-31T15:00:10Z')
    ]
    for item in items:
        table.put_item(Item=item)

    login(client)
    response = client.get(JOBS_URI, query_string={'start': '2019-12-31T15:00:00Z'})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json['jobs']) == 2
    assert items[0] in response.json['jobs']
    assert items[1] in response.json['jobs']

    response = client.get(JOBS_URI, query_string={'start': '2019-12-31T15:00:10Z'})
    assert response.status_code == status.HTTP_200_OK
    assert response.json == {'jobs': [items[1]]}

    response = client.get(JOBS_URI, query_string={'start': '2019-12-31T15:00:11Z'})
    assert response.status_code == status.HTTP_200_OK
    assert response.json == {'jobs': []}


def test_list_jobs_by_start_timezones(client, table):
    items = [
        make_db_record('0ddaeb98-7636-494d-9496-03ea4a7df266', request_time='2019-12-31T10:00:00Z'),
        make_db_record('27836b79-e5b2-4d8f-932f-659724ea02c3', request_time='2019-12-31T10:00:10Z')
    ]
    for item in items:
        table.put_item(Item=item)

    login(client)
    response = client.get(JOBS_URI, query_string={'start': '2019-12-31T09:00:00+01:00'})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json['jobs']) == 2
    assert items[0] in response.json['jobs']
    assert items[1] in response.json['jobs']
