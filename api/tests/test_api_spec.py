from conftest import AUTH_COOKIE, DEFAULT_USERNAME, JOBS_URI, auth, login, make_job, submit_batch
from flask_api import status


def test_not_logged_in(client):
    response = submit_batch(client)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.get(JOBS_URI)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.head(JOBS_URI)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_logged_in_not_authorized(client):
    login(client, authorized=False)
    response = submit_batch(client)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert DEFAULT_USERNAME in response.get_json()['detail']


def test_invalid_cookie(client):
    client.set_cookie('localhost', AUTH_COOKIE, 'garbage I say!!! GARGBAGE!!!')
    response = submit_batch(client)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_expired_cookie(client):
    client.set_cookie('localhost', AUTH_COOKIE, auth.get_mock_jwt_cookie('user', -1))
    response = submit_batch(client)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_good_granule_names(client, table):
    login(client)
    batch = [
        make_job('S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_200_OK

    batch = [
        make_job('S1A_IW_SLC__1SSH_20150608T205059_20150608T205126_006287_0083E8_C4F0')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_200_OK


def test_bad_granule_names(client):
    login(client)

    batch = [
        make_job('foo')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    batch = [
        make_job('S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E3')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    batch = [
        make_job('S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38_')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_bad_beam_modes(client):
    login(client)

    batch = [
        make_job('S1B_S3_SLC__1SDV_20200604T091417_20200604T091430_021882_029879_5765')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    batch = [
        make_job('S1B_WV_SLC__1SSV_20200519T140110_20200519T140719_021651_0291AA_2A86')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    batch = [
        make_job('S1B_EW_SLC__1SDH_20200605T065551_20200605T065654_021895_0298DC_EFB5')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_bad_product_types(client):
    login(client)

    batch = [
        make_job('S1A_IW_GRDH_1SDV_20200604T190627_20200604T190652_032871_03CEB7_56F3')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    batch = [
        make_job('S1B_IW_OCN__2SDV_20200518T220815_20200518T220851_021642_02915F_B404')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    batch = [
        make_job('S1B_IW_RAW__0SDV_20200605T145138_20200605T145210_021900_029903_AFF4')
    ]
    response = submit_batch(client, batch)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_jobs_bad_method(client):
    response = client.put(JOBS_URI)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    response = client.delete(JOBS_URI)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_no_route(client):
    response = client.get('/no/such/path')
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_cors_no_origin(client):
    response = client.post(JOBS_URI)
    assert 'Access-Control-Allow-Origin' not in response.headers
    assert 'Access-Control-Allow-Credentials' not in response.headers


def test_cors_bad_origins(client):
    response = client.post(JOBS_URI, headers={'Origin': 'https://www.google.com'})
    assert 'Access-Control-Allow-Origin' not in response.headers
    assert 'Access-Control-Allow-Credentials' not in response.headers

    response = client.post(JOBS_URI, headers={'Origin': 'https://www.alaska.edu'})
    assert 'Access-Control-Allow-Origin' not in response.headers
    assert 'Access-Control-Allow-Credentials' not in response.headers


def test_cors_good_origins(client):
    response = client.post(JOBS_URI, headers={'Origin': 'https://search.asf.alaska.edu'})
    assert response.headers['Access-Control-Allow-Origin'] == 'https://search.asf.alaska.edu'
    assert response.headers['Access-Control-Allow-Credentials'] == 'true'

    response = client.post(JOBS_URI, headers={'Origin': 'https://search-test.asf.alaska.edu'})
    assert response.headers['Access-Control-Allow-Origin'] == 'https://search-test.asf.alaska.edu'
    assert response.headers['Access-Control-Allow-Credentials'] == 'true'

    response = client.post(JOBS_URI, headers={'Origin': 'http://local.asf.alaska.edu'})
    assert response.headers['Access-Control-Allow-Origin'] == 'http://local.asf.alaska.edu'
    assert response.headers['Access-Control-Allow-Credentials'] == 'true'
