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
        make_db_record('27836b79-e5b2-4d8f-932f-659724ea02c3', request_time='2019-12-31T15:00:10Z'),
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


def test_list_jobs_by_start_formats(client, table):
    items = [
        make_db_record('874f7533-807d-4b20-afe1-27b5b6fc9d6c', request_time='2019-12-31T10:00:00Z'),
        make_db_record('0ddaeb98-7636-494d-9496-03ea4a7df266', request_time='2019-12-31T10:00:10Z'),
        make_db_record('27836b79-e5b2-4d8f-932f-659724ea02c3', request_time='2019-12-31T10:00:20Z'),
    ]
    for item in items:
        table.put_item(Item=item)

    dates = [
        '2019-12-31T10:00:10Z',
        '2019-12-31T10:00:10.000Z',
        '2019-12-31T10:00:10.999999Z',
        '2019-12-31T11:00:10+01:00',
        '2019-12-31T09:00:10-01:00',
        '2020-01-01T09:00:10+23:00',
        '2019-12-30T11:00:10-23:00',
        '2019-12-31T11:30:10+01:30',
    ]
    login(client)
    for date in dates:
        response = client.get(JOBS_URI, query_string={'start': date})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json['jobs']) == 2
        assert items[1] in response.json['jobs']
        assert items[2] in response.json['jobs']


def test_bad_date_formats(client):
    bad_dates = [
      '',
      'foo',
      '2020-13-01T00:00:00Z',
      '01-JAN-2020',
      '01/01/2020',
      '2020-01-01'
      '2020-01-01T00:00Z',
      '2020-01-01T00:00:00',
      '2020-01-01T00:00:00+01',
      '2020-01-01T00:00:00+0100',
      '2020-01-01T00:00:00-24:00',
    ]
    login(client)
    for bad_date in bad_dates:
        response = client.get(JOBS_URI, query_string={'start': bad_date})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
