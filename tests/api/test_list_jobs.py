from http import HTTPStatus
from unittest import mock
from urllib.parse import unquote

from api.conftest import JOBS_URI, list_have_same_elements, login, make_db_record


def test_list_jobs(client, tables):
    files = [
        {
            'filename': 'foo.txt',
            'size': 123,
            'url': 'https://mybucket.s3.us-west-2.amazonaws.com/prefix/foo.txt',
            's3': {
                'bucket': 'mybucket',
                'key': 'prefix/foo.txt'
            },
        },
        {
            'filename': 'bar.png',
            'size': 0,
            'url': 'https://mybucket.s3.us-west-2.amazonaws.com/prefix/bar.png',
            's3': {
                'bucket': 'mybucket',
                'key': 'prefix/bar.png'
            },
        },
    ]
    browse_images = ['https://mybucket.s3.us-west-2.amazonaws.com/prefix/browse/foo.png']
    thumbnail_images = []
    items = [
        make_db_record('0ddaeb98-7636-494d-9496-03ea4a7df266', user_id='user_with_jobs'),
        make_db_record(job_id='27836b79-e5b2-4d8f-932f-659724ea02c3', user_id='user_with_jobs', files=files,
                       browse_images=browse_images, thumbnail_images=thumbnail_images)
    ]
    for item in items:
        tables['jobs_table'].put_item(Item=item)

    login(client, 'user_with_jobs')
    response = client.get(JOBS_URI)
    assert response.status_code == HTTPStatus.OK
    assert 'jobs' in response.json
    assert list_have_same_elements(response.json['jobs'], items)

    login(client, 'user_without_jobs')
    response = client.get(JOBS_URI)
    assert response.status_code == HTTPStatus.OK
    assert response.json == {'jobs': []}


def test_list_jobs_by_name(client, tables):
    items = [
        make_db_record('0ddaeb98-7636-494d-9496-03ea4a7df266', name='item1'),
        make_db_record('27836b79-e5b2-4d8f-932f-659724ea02c3', name='item2')
    ]
    for item in items:
        tables['jobs_table'].put_item(Item=item)

    login(client)
    response = client.get(JOBS_URI, query_string={'name': 'item1'})
    assert response.status_code == HTTPStatus.OK
    assert response.json == {'jobs': [items[0]]}

    response = client.get(JOBS_URI, query_string={'name': 'item does not exist'})
    assert response.status_code == HTTPStatus.OK
    assert response.json == {'jobs': []}


def test_list_jobs_by_type(client, tables):
    items = [
        make_db_record('0ddaeb98-7636-494d-9496-03ea4a7df266', job_type='RTC_GAMMA'),
        make_db_record('874f7533-807d-4b20-afe1-27b5b6fc9d6c', job_type='RTC_GAMMA'),
        make_db_record('27836b79-e5b2-4d8f-932f-659724ea02c3', job_type='INSAR_GAMMA'),
    ]
    for item in items:
        tables['jobs_table'].put_item(Item=item)

    login(client)
    response = client.get(JOBS_URI, query_string={'job_type': 'RTC_GAMMA'})
    assert response.status_code == HTTPStatus.OK
    assert list_have_same_elements(response.json['jobs'], items[:2])

    response = client.get(JOBS_URI, query_string={'job_type': 'INSAR_GAMMA'})
    assert response.status_code == HTTPStatus.OK
    assert response.json == {'jobs': [items[2]]}

    response = client.get(JOBS_URI, query_string={'job_type': 'FOOBAR'})
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_list_jobs_by_status(client, tables):
    items = [
        make_db_record('0ddaeb98-7636-494d-9496-03ea4a7df266', status_code='RUNNING'),
        make_db_record('27836b79-e5b2-4d8f-932f-659724ea02c3', status_code='SUCCEEDED')
    ]
    for item in items:
        tables['jobs_table'].put_item(Item=item)

    login(client)
    response = client.get(JOBS_URI, query_string={'status_code': 'RUNNING'})
    assert response.status_code == HTTPStatus.OK
    assert response.json == {'jobs': [items[0]]}

    response = client.get(JOBS_URI, query_string={'status_code': 'FAILED'})
    assert response.status_code == HTTPStatus.OK
    assert response.json == {'jobs': []}


def test_list_jobs_bad_status(client):
    login(client)

    response = client.get(JOBS_URI, query_string={'status_code': 'BAD'})
    assert response.status_code == HTTPStatus.BAD_REQUEST

    response = client.get(JOBS_URI, query_string={'status_code': ''})
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_list_jobs_date_start_and_end(client, tables):
    items = [
        make_db_record('874f7533-807d-4b20-afe1-27b5b6fc9d6c', request_time='2019-12-31T10:00:09+00:00'),
        make_db_record('0ddaeb98-7636-494d-9496-03ea4a7df266', request_time='2019-12-31T10:00:10+00:00'),
        make_db_record('27836b79-e5b2-4d8f-932f-659724ea02c3', request_time='2019-12-31T10:00:11+00:00'),
    ]
    for item in items:
        tables['jobs_table'].put_item(Item=item)

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
        assert response.status_code == HTTPStatus.OK
        assert list_have_same_elements(response.json['jobs'], items[1:])

        response = client.get(JOBS_URI, query_string={'end': date})
        assert response.status_code == HTTPStatus.OK
        assert list_have_same_elements(response.json['jobs'], items[:2])

        response = client.get(JOBS_URI, query_string={'start': date, 'end': date})
        assert response.status_code == HTTPStatus.OK
        assert response.json == {'jobs': [items[1]]}


def test_bad_date_formats(client):
    datetime_parameters = ['start', 'end']
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
    for datetime_parameter in datetime_parameters:
        for bad_date in bad_dates:
            response = client.get(JOBS_URI, query_string={datetime_parameter: bad_date})
            assert response.status_code == HTTPStatus.BAD_REQUEST


def test_list_paging(client):
    login(client)
    mock_response = ([], {'foo': 1, 'bar': 2})
    with mock.patch('hyp3_api.dynamo.query_jobs', return_value=mock_response):
        response = client.get(JOBS_URI)
        assert unquote(response.json['next']) == 'http://localhost/jobs?start_token=eyJmb28iOiAxLCAiYmFyIjogMn0='
