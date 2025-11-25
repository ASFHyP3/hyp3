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
