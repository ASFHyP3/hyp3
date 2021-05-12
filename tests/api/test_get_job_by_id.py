from http import HTTPStatus

from api.conftest import JOBS_URI, login, make_db_record


def test_get_job_by_id(client, tables):
    job_id = '0ddaeb98-7636-494d-9496-03ea4a7df266'
    record = make_db_record(job_id, name='item1')

    tables['jobs_table'].put_item(Item=record)

    login(client)
    response = client.get(f'{JOBS_URI}/{job_id}')
    assert response.status_code == HTTPStatus.OK
    assert response.json == record

    job_id = '0ddaeb98-7636-494d-9496-03ea4a7df200'
    response = client.get(f'{JOBS_URI}/{job_id}')
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert job_id in response.json['detail']

    job_id = 'boogers'
    response = client.get(f'{JOBS_URI}/{job_id}')
    assert response.status_code == HTTPStatus.BAD_REQUEST
