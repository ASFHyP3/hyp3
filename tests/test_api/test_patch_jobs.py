from http import HTTPStatus

from test_api.conftest import JOBS_URI, login


def test_patch_jobs(client, tables):
    table_items = [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'name': 'oldname1',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': '40183948-48a1-42d2-a96b-ce44fbba301b',
            'name': 'oldname2',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': 'b0dd41bc-5597-4a58-afe4-81f30e53bbb0',
            'name': 'oldname3',
            'somefield': 'somevalue',
            'user_id': 'user2',
        },
    ]

    for item in table_items:
        tables.jobs_table.put_item(Item=item)

    login(client, 'user1')

    response = client.patch(
        JOBS_URI,
        json={
            'job_ids': [
                '33d85ea0-9342-4c21-ae59-5bec3f71612c',
                '40183948-48a1-42d2-a96b-ce44fbba301b',
            ],
            'name': 'newname',
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json == {}
    assert tables.jobs_table.scan()['Items'] == [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'name': 'newname',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': '40183948-48a1-42d2-a96b-ce44fbba301b',
            'name': 'newname',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': 'b0dd41bc-5597-4a58-afe4-81f30e53bbb0',
            'name': 'oldname3',
            'somefield': 'somevalue',
            'user_id': 'user2',
        },
    ]

    response = client.patch(
        JOBS_URI,
        json={
            'job_ids': [
                '33d85ea0-9342-4c21-ae59-5bec3f71612c',
                '40183948-48a1-42d2-a96b-ce44fbba301b',
            ],
            'name': None,
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json == {}
    assert tables.jobs_table.scan()['Items'] == [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': '40183948-48a1-42d2-a96b-ce44fbba301b',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': 'b0dd41bc-5597-4a58-afe4-81f30e53bbb0',
            'name': 'oldname3',
            'somefield': 'somevalue',
            'user_id': 'user2',
        },
    ]

    response = client.patch(
        JOBS_URI,
        json={
            'job_ids': [
                '33d85ea0-9342-4c21-ae59-5bec3f71612c',
                '40183948-48a1-42d2-a96b-ce44fbba301b',
            ],
            'name': 'anothernewname',
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json == {}
    assert tables.jobs_table.scan()['Items'] == [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'name': 'anothernewname',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': '40183948-48a1-42d2-a96b-ce44fbba301b',
            'name': 'anothernewname',
            'somefield': 'somevalue',
            'user_id': 'user1',
        },
        {
            'job_id': 'b0dd41bc-5597-4a58-afe4-81f30e53bbb0',
            'name': 'oldname3',
            'somefield': 'somevalue',
            'user_id': 'user2',
        },
    ]


def test_job_ids_length(client, tables):
    table_items = [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'name': 'oldname',
            'user_id': 'user1',
        },
    ]

    for item in table_items:
        tables.jobs_table.put_item(Item=item)

    login(client, 'user1')

    response = client.patch(
        JOBS_URI,
        json={
            'job_ids': ['33d85ea0-9342-4c21-ae59-5bec3f71612c'] * 100,
            'name': 'newname',
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json == {}
    assert tables.jobs_table.scan()['Items'] == [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'name': 'newname',
            'user_id': 'user1',
        },
    ]

    response = client.patch(
        JOBS_URI,
        json={
            'job_ids': ['33d85ea0-9342-4c21-ae59-5bec3f71612c'] * 101,
            'name': 'newname2',
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json['detail'] == 'Cannot update more than 100 jobs'

    response = client.patch(
        JOBS_URI,
        json={
            'job_ids': [],
            'name': 'newname2',
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json['detail'] == 'Must provide at least one job ID'

    assert tables.jobs_table.scan()['Items'] == [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'name': 'newname',
            'user_id': 'user1',
        },
    ]


def test_job_not_found(client, tables):
    table_items = [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'name': 'oldname',
            'user_id': 'user1',
        },
    ]
    for item in table_items:
        tables.jobs_table.put_item(Item=item)

    login(client, 'user1')

    response = client.patch(JOBS_URI, json={'job_ids': ['40183948-48a1-42d2-a96b-ce44fbba301b'], 'name': 'newname'})
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json['detail'] == 'Job 40183948-48a1-42d2-a96b-ce44fbba301b does not exist'
    assert tables.jobs_table.scan()['Items'] == [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'name': 'oldname',
            'user_id': 'user1',
        },
    ]


def test_different_user(client, tables):
    table_items = [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'name': 'oldname',
            'user_id': 'user1',
        },
        {
            'job_id': '40183948-48a1-42d2-a96b-ce44fbba301b',
            'name': 'oldname',
            'user_id': 'user2',
        },
    ]
    for item in table_items:
        tables.jobs_table.put_item(Item=item)

    login(client, 'user1')

    response = client.patch(JOBS_URI, json={'job_ids': ['40183948-48a1-42d2-a96b-ce44fbba301b'], 'name': 'newname'})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert (
        response.json['detail']
        == 'You cannot modify job 40183948-48a1-42d2-a96b-ce44fbba301b because it belongs to a different user'
    )

    response = client.patch(JOBS_URI, json={'job_ids': ['40183948-48a1-42d2-a96b-ce44fbba301b'], 'name': None})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert (
        response.json['detail']
        == 'You cannot modify job 40183948-48a1-42d2-a96b-ce44fbba301b because it belongs to a different user'
    )

    assert tables.jobs_table.scan()['Items'] == [
        {
            'job_id': '33d85ea0-9342-4c21-ae59-5bec3f71612c',
            'name': 'oldname',
            'user_id': 'user1',
        },
        {
            'job_id': '40183948-48a1-42d2-a96b-ce44fbba301b',
            'name': 'oldname',
            'user_id': 'user2',
        },
    ]


def test_patch_jobs_schema(client, tables):
    login(client, 'user1')

    response = client.patch(JOBS_URI, json={'name': 'newname'})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "'job_ids' is a required property" in response.json['detail']

    response = client.patch(JOBS_URI, json={'job_ids': ['33d85ea0-9342-4c21-ae59-5bec3f71612c']})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "'name' is a required property" in response.json['detail']

    response = client.patch(JOBS_URI, json={'job_ids': ['33d85ea0-9342-4c21-ae59-5bec3f71612c'], 'foo': 'bar'})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "'foo' was unexpected" in response.json['detail']

    response = client.patch(JOBS_URI, json={'job_ids': ['foo'], 'name': 'newname'})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "'foo' is not a 'uuid'" in response.json['detail']

    response = client.patch(JOBS_URI, json={'job_ids': ['33d85ea0-9342-4c21-ae59-5bec3f71612c'], 'name': ''})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "'' should be non-empty" in response.json['detail']

    response = client.patch(JOBS_URI, json={'job_ids': ['33d85ea0-9342-4c21-ae59-5bec3f71612c'], 'name': '-' * 100})
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json['detail'] == 'Job 33d85ea0-9342-4c21-ae59-5bec3f71612c does not exist'

    response = client.patch(JOBS_URI, json={'job_ids': ['33d85ea0-9342-4c21-ae59-5bec3f71612c'], 'name': '-' * 101})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'is too long' in response.json['detail']

    response = client.patch(JOBS_URI, json={'job_ids': ['33d85ea0-9342-4c21-ae59-5bec3f71612c'], 'name': True})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "True is not of type 'string'" in response.json['detail']
