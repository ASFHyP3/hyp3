from http import HTTPStatus

from test_api.conftest import JOBS_URI, login


def test_patch_job(client, tables):
    table_items = [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': '40183948-48a1-42d2-a96b-ce44fbba301b',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user2',
        },
    ]
    for item in table_items:
        tables.jobs_table.put_item(Item=item)

    login(client, 'user1')

    response = client.patch(f'{JOBS_URI}/33d85ea0-9342-4c21-ae59-5bec3f71612c', json={'name': 'newname'})

    assert response.status_code == HTTPStatus.OK
    assert response.json == {
        'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
        'name': 'newname',
        'somefield': 'somevalue',
        'user_id': 'user1',
    }
    assert tables.jobs_table.scan()['Items'] == [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'name': 'newname',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': '40183948-48a1-42d2-a96b-ce44fbba301b',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user2',
        },
    ]

    response = client.patch(f'{JOBS_URI}/33d85ea0-9342-4c21-ae59-5bec3f71612c', json={'name': None})

    assert response.status_code == HTTPStatus.OK
    assert response.json == {
        'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
        'somefield': 'somevalue',
        'user_id': 'user1',
    }
    assert tables.jobs_table.scan()['Items'] == [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': '40183948-48a1-42d2-a96b-ce44fbba301b',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user2',
        },
    ]

    response = client.patch(f'{JOBS_URI}/33d85ea0-9342-4c21-ae59-5bec3f71612c', json={'name': 'anothernewname'})

    assert response.status_code == HTTPStatus.OK
    assert response.json == {
        'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
        'name': 'anothernewname',
        'somefield': 'somevalue',
        'user_id': 'user1',
    }
    assert tables.jobs_table.scan()['Items'] == [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'name': 'anothernewname',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': '40183948-48a1-42d2-a96b-ce44fbba301b',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user2',
        },
    ]


def test_patch_job_not_found(client, tables):
    table_items = [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
    ]
    for item in table_items:
        tables.jobs_table.put_item(Item=item)

    login(client, 'user1')

    response = client.patch(f'{JOBS_URI}/40183948-48a1-42d2-a96b-ce44fbba301b', json={'name': 'newname'})
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json['detail'] == 'Job 40183948-48a1-42d2-a96b-ce44fbba301b does not exist'

    assert tables.jobs_table.scan()['Items'] == [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
    ]


def test_patch_job_different_user(client, tables):
    table_items = [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': '40183948-48a1-42d2-a96b-ce44fbba301b',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user2',
        },
    ]
    for item in table_items:
        tables.jobs_table.put_item(Item=item)

    login(client, 'user1')

    response = client.patch(f'{JOBS_URI}/40183948-48a1-42d2-a96b-ce44fbba301b', json={'name': 'newname'})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json['detail'] == "You cannot modify a different user's job"

    response = client.patch(f'{JOBS_URI}/40183948-48a1-42d2-a96b-ce44fbba301b', json={'name': None})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json['detail'] == "You cannot modify a different user's job"

    assert tables.jobs_table.scan()['Items'] == [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': '40183948-48a1-42d2-a96b-ce44fbba301b',
            'name': 'oldname',
            'somefield': 'somevalue',
            'user_id': 'user2',
        },
    ]


def test_patch_job_schema(client, tables):
    login(client, 'user1')

    response = client.patch(f'{JOBS_URI}/33d85ea0-9342-4c21-ae59-5bec3f71612c', json={})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert '{} should be non-empty' in response.json['detail']

    response = client.patch(f'{JOBS_URI}/33d85ea0-9342-4c21-ae59-5bec3f71612c', json={'foo': 'bar'})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "'foo' was unexpected" in response.json['detail']

    response = client.patch(f'{JOBS_URI}/33d85ea0-9342-4c21-ae59-5bec3f71612c', json={'name': ''})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "'' should be non-empty" in response.json['detail']

    response = client.patch(f'{JOBS_URI}/33d85ea0-9342-4c21-ae59-5bec3f71612c', json={'name': '-' * 100})
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json['detail'] == 'Job 33d85ea0-9342-4c21-ae59-5bec3f71612c does not exist'

    response = client.patch(f'{JOBS_URI}/33d85ea0-9342-4c21-ae59-5bec3f71612c', json={'name': '-' * 101})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'is too long' in response.json['detail']

    response = client.patch(f'{JOBS_URI}/33d85ea0-9342-4c21-ae59-5bec3f71612c', json={'name': True})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "True is not of type 'string'" in response.json['detail']
