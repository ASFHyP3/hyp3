from datetime import datetime, timezone
from http import HTTPStatus

from test_api.conftest import DEFAULT_USERNAME, login, make_job, setup_requests_mock, submit_batch

from dynamo.util import format_time


def test_submit_one_job(client, tables):
    login(client)
    batch = [make_job()]
    setup_requests_mock(batch)
    response = submit_batch(client, batch)
    assert response.status_code == HTTPStatus.OK
    jobs = response.json['jobs']
    assert len(jobs) == 1
    assert jobs[0]['status_code'] == 'PENDING'
    assert jobs[0]['request_time'] <= format_time(datetime.now(timezone.utc))
    assert jobs[0]['user_id'] == DEFAULT_USERNAME


def test_submit_insar_gamma(client, tables):
    login(client)
    granules = [
        'S1A_IW_SLC__1SDV_20200720T172109_20200720T172128_033541_03E2FB_341F',
        'S1A_IW_SLC__1SDV_20200813T172110_20200813T172129_033891_03EE3F_2C3E',
    ]

    job = make_job(
        granules=granules,
        job_type='INSAR_GAMMA',
    )
    batch = [job]
    setup_requests_mock(batch)
    response = submit_batch(client, batch=batch)
    assert response.status_code == HTTPStatus.OK

    job = make_job(
        granules=granules,
        job_type='INSAR_GAMMA',
        parameters={
            'looks': '10x2',
            'include_inc_map': True,
            'include_look_vectors': True,
            'include_los_displacement': False,
            'include_displacement_maps': True,
            'include_dem': True,
            'include_wrapped_phase': True,
            'apply_water_mask': True,
        },
    )
    batch = [job]
    setup_requests_mock(batch)
    response = submit_batch(client, batch=batch)
    assert response.status_code == HTTPStatus.OK


def test_submit_autorift(client, tables):
    login(client)
    job = make_job(
        [
            'S1A_IW_SLC__1SDV_20200720T172109_20200720T172128_033541_03E2FB_341F',
            'S1A_IW_SLC__1SDV_20200813T172110_20200813T172129_033891_03EE3F_2C3E',
        ],
        job_type='AUTORIFT',
    )
    batch = [job]
    setup_requests_mock(batch)
    response = submit_batch(client, batch)
    assert response.status_code == HTTPStatus.OK


def test_submit_multiple_job_types(client, tables):
    login(client)
    rtc_gamma_job = make_job()
    insar_gamma_job = make_job(
        [
            'S1A_IW_SLC__1SDV_20200720T172109_20200720T172128_033541_03E2FB_341F',
            'S1A_IW_SLC__1SDV_20200813T172110_20200813T172129_033891_03EE3F_2C3E'
        ],
        job_type='INSAR_GAMMA'
    )
    autorift_job = make_job(
        [
            'S1A_IW_SLC__1SDV_20200720T172109_20200720T172128_033541_03E2FB_341F',
            'S1A_IW_SLC__1SDV_20200813T172110_20200813T172129_033891_03EE3F_2C3E'
        ],
        job_type='AUTORIFT'
    )
    batch = [rtc_gamma_job, insar_gamma_job, autorift_job]
    setup_requests_mock(batch)
    response = submit_batch(client, batch)
    assert response.status_code == HTTPStatus.OK


def test_submit_many_jobs(client, tables):
    max_jobs = 25
    login(client)

    batch = [make_job() for ii in range(max_jobs)]
    setup_requests_mock(batch)

    response = submit_batch(client, batch)
    assert response.status_code == HTTPStatus.OK
    jobs = response.json['jobs']
    distinct_request_times = {job['request_time'] for job in jobs}
    assert len(jobs) == max_jobs
    assert len(distinct_request_times) == 1

    batch.append(make_job())
    response = submit_batch(client, batch)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_submit_exceeds_remaining_credits(client, tables, monkeypatch):
    login(client)
    monkeypatch.setenv('DEFAULT_CREDITS_PER_USER', '25')

    batch1 = [make_job() for _ in range(20)]
    setup_requests_mock(batch1)

    response1 = submit_batch(client, batch1)
    assert response1.status_code == HTTPStatus.OK

    batch2 = [make_job() for _ in range(10)]
    setup_requests_mock(batch2)

    response2 = submit_batch(client, batch2)
    assert response2.status_code == HTTPStatus.BAD_REQUEST
    assert response2.json['detail'] == 'These jobs would cost 10.0 credits, but you have only 5.0 remaining.'


def test_submit_unapproved_user(client, tables):
    login(client)

    batch = [make_job()]
    setup_requests_mock(batch)

    response = submit_batch(client, batch)
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json['detail'] == 'User test_username is not approved for processing'

    tables.users_table.put_item(Item={'user_id': 'test_username', 'remaining_credits': 1, 'approved': True})
    response = submit_batch(client, batch)
    assert response.status_code == HTTPStatus.OK


def test_submit_without_jobs(client):
    login(client)
    batch = []
    response = submit_batch(client, batch)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_submit_job_without_name(client, tables):
    login(client)
    batch = [
        make_job(name=None)
    ]
    setup_requests_mock(batch)

    response = submit_batch(client, batch)
    assert response.status_code == HTTPStatus.OK


def test_submit_job_with_empty_name(client):
    login(client)
    batch = [
        make_job(name='')
    ]
    setup_requests_mock(batch)
    response = submit_batch(client, batch)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_submit_job_with_long_name(client):
    login(client)
    batch = [
        make_job(name='X' * 101)
    ]
    setup_requests_mock(batch)
    response = submit_batch(client, batch)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_submit_job_without_granules(client):
    login(client)

    for job_type in ['AUTORIFT', 'INSAR_GAMMA', 'RTC_GAMMA']:
        batch = [
            {
                'job_type': job_type,
                'job_parameters': {},
            },
        ]
        response = submit_batch(client, batch)
        assert response.status_code == HTTPStatus.BAD_REQUEST


def test_submit_job_granule_does_not_exist(client, tables):
    batch = [
        make_job(['S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38']),
        make_job(['S1A_IW_SLC__1SDV_20200610T173646_20200610T173704_032958_03D14C_5F2B'])
    ]
    setup_requests_mock(batch)
    batch.append(make_job(['S1A_IW_SLC__1SDV_20200610T173646_20200610T173704_032958_03D14C_5F2A']))

    login(client)
    response = submit_batch(client, batch)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json['title'] == 'Bad Request'
    assert response.json['detail'] == 'Some requested scenes could not be found: ' \
                                      'S1A_IW_SLC__1SDV_20200610T173646_20200610T173704_032958_03D14C_5F2A'


def test_submit_good_rtc_granule_names(client, tables):
    login(client)
    good_granule_names = [
        'S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38',
        'S1A_IW_SLC__1SSH_20150608T205059_20150608T205126_006287_0083E8_C4F0',
        'S1A_IW_GRDH_1SDV_20200604T190627_20200604T190652_032871_03CEB7_56F3',
        'S1A_IW_GRDH_1SSH_20171122T184459_20171122T184524_019381_020DD8_B825',
    ]
    for granule in good_granule_names:
        batch = [
            make_job([granule]),
        ]
        setup_requests_mock(batch)
        response = submit_batch(client, batch)
        assert response.status_code == HTTPStatus.OK


def test_submit_bad_rtc_granule_names(client):
    login(client)
    bad_granule_names = [
        'foo',
        'S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E3',
        'S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38_',
        # bad mission
        'S1C_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38',
        # bad beam modes
        'S1B_S3_SLC__1SDV_20200604T091417_20200604T091430_021882_029879_5765',
        'S1B_WV_SLC__1SSV_20200519T140110_20200519T140719_021651_0291AA_2A86',
        'S1B_EW_SLC__1SDH_20200605T065551_20200605T065654_021895_0298DC_EFB5',
        'S1A_EW_GRDH_1SDH_20171121T103939_20171121T104044_019362_020D26_CF9A',
        'S1B_S1_GRDH_1SDH_20171024T121032_20171024T121101_007971_00E153_F8F2',
        # bad product types
        'S1B_IW_OCN__2SDV_20200518T220815_20200518T220851_021642_02915F_B404',
        'S1B_IW_RAW__0SDV_20200605T145138_20200605T145210_021900_029903_AFF4',
        'S1A_IW_GRDM_1SDH_20190624T101121_20190624T101221_027820_0323FF_79E4',
        # bad polarizations
        'S1A_IW_SLC__1SHH_20150512T135706_20150512T135734_005889_007957_EE69',
        'S1A_IW_SLC__1SVH_20150513T032111_20150513T032139_005897_007989_686E',
        'S1A_IW_SLC__1SVV_20150622T103100_20150622T103120_006485_008992_BBB5',
        # other missions
        'S2A_MSIL1C_20200627T150921_N0209_R025_T22WEB_20200627T170912',
        'S2B_22WEB_20200612_0_L1C',
        'LC08_L1TP_009011_20200820_20200905_02_T1',
        'LC09_L1GT_215109_20220125_20220125_02_T2',
    ]
    for granule in bad_granule_names:
        batch = [
            make_job(granule),
        ]
        setup_requests_mock(batch)
        response = submit_batch(client, batch)
        assert response.status_code == HTTPStatus.BAD_REQUEST


def test_submit_good_autorift_granule_names(client, tables):
    login(client)
    good_granule_names = [
        'S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38',
        'S1A_IW_SLC__1SSH_20150608T205059_20150608T205126_006287_0083E8_C4F0',
        'S2A_MSIL1C_20200627T150921_N0209_R025_T22WEB_20200627T170912',
        'S2B_MSIL1C_20200612T150759_N0209_R025_T22WEB_20200612T184700',
        'LT05_L1TP_233248_19950801_19950902_01_T2',
        'LE07_L1GT_233095_20200102_20200822_02_T2',
        'LO08_L1GT_043001_20201106_20201110_02_T2',
        'LC09_L1GT_215109_20220125_20220125_02_T2',
        'LO09_L1GT_215109_20220210_20220210_02_T2',
    ]
    for granule in good_granule_names:
        batch = [
            make_job(job_type='AUTORIFT', granules=[granule, granule]),
        ]
        setup_requests_mock(batch)
        response = submit_batch(client, batch)
        assert response.status_code == HTTPStatus.OK


def test_submit_bad_autorift_granule_names(client):
    login(client)
    bad_granule_names = [
        'foo',
        'S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E3',
        'S1B_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38_',
        # bad mission
        'S1C_IW_SLC__1SDV_20200604T082207_20200604T082234_021881_029874_5E38',
        # bad beam modes
        'S1B_S3_SLC__1SDV_20200604T091417_20200604T091430_021882_029879_5765',
        'S1B_WV_SLC__1SSV_20200519T140110_20200519T140719_021651_0291AA_2A86',
        'S1B_EW_SLC__1SDH_20200605T065551_20200605T065654_021895_0298DC_EFB5',
        'S1A_EW_GRDH_1SDH_20171121T103939_20171121T104044_019362_020D26_CF9A',
        'S1B_S1_GRDH_1SDH_20171024T121032_20171024T121101_007971_00E153_F8F2',
        # bad product types
        'S1B_IW_OCN__2SDV_20200518T220815_20200518T220851_021642_02915F_B404',
        'S1B_IW_RAW__0SDV_20200605T145138_20200605T145210_021900_029903_AFF4',
        'S1A_IW_GRDM_1SDH_20190624T101121_20190624T101221_027820_0323FF_79E4',
        'S1A_IW_GRDH_1SDV_20200604T190627_20200604T190652_032871_03CEB7_56F3',
        'S1A_IW_GRDH_1SSH_20171122T184459_20171122T184524_019381_020DD8_B825',
        # Element 84 S2 names
        'S2B_22WEB_20200612_0_L1C',
        'S2A_22XEQ_20190610_10_L1C',
        # bad L8 sensor mode
        'LT08_L1GT_041001_20200125_20200925_02_T2',
        'LT09_L1GT_215109_20220125_20220125_02_T2',
        # wrong Landsat data level
        'LE07_L2SP_233095_20200102_20200822_02_T2',
        # S2 name too long
        'S2B_22XEQ_20190610_11_XL1C',
        'S2A_22XEQ_20190610_10_XL1C',
        # S2 name too short
        'S2B_22XEQ_20190610_L1C',
        'S2A_22XEQ_20190610_L1C',
    ]
    for granule in bad_granule_names:
        batch = [
            make_job(job_type='AUTORIFT', granules=[granule, granule]),
        ]
        setup_requests_mock(batch)
        response = submit_batch(client, batch)
        assert response.status_code == HTTPStatus.BAD_REQUEST


def test_submit_mixed_job_parameters(client, tables):
    login(client)

    rtc_parameters = {
        'resolution': 30.0,
    }
    insar_parameters = {
        'looks': '20x4',
    }
    granule_pair = [
        'S1A_IW_SLC__1SDV_20200527T195012_20200527T195028_032755_03CB56_3D96',
        'S1A_IW_SLC__1SDV_20200515T195012_20200515T195027_032580_03C609_4EBA'
    ]

    job = make_job(job_type='RTC_GAMMA', parameters=rtc_parameters)
    batch = [job]
    setup_requests_mock(batch)
    response = submit_batch(client, batch)
    assert response.status_code == HTTPStatus.OK

    job = make_job(job_type='RTC_GAMMA', parameters=insar_parameters)
    response = submit_batch(client, batch=[job])
    assert response.status_code == HTTPStatus.BAD_REQUEST

    job = make_job(job_type='RTC_GAMMA', parameters={**rtc_parameters, **insar_parameters})
    response = submit_batch(client, batch=[job])
    assert response.status_code == HTTPStatus.BAD_REQUEST

    job = make_job(granules=granule_pair, job_type='INSAR_GAMMA', parameters=insar_parameters)
    batch = [job]
    setup_requests_mock(batch)
    response = submit_batch(client, batch)
    assert response.status_code == HTTPStatus.OK

    job = make_job(granules=granule_pair, job_type='INSAR_GAMMA', parameters=rtc_parameters)
    response = submit_batch(client, batch=[job])
    assert response.status_code == HTTPStatus.BAD_REQUEST

    job = make_job(granules=granule_pair, job_type='INSAR_GAMMA', parameters={**rtc_parameters, **insar_parameters})
    response = submit_batch(client, batch=[job])
    assert response.status_code == HTTPStatus.BAD_REQUEST

    job = make_job(granules=granule_pair, job_type='AUTORIFT')
    batch = [job]
    setup_requests_mock(batch)
    response = submit_batch(client, batch)
    assert response.status_code == HTTPStatus.OK

    job = make_job(granules=granule_pair, job_type='AUTORIFT', parameters=rtc_parameters)
    response = submit_batch(client, batch=[job])
    assert response.status_code == HTTPStatus.BAD_REQUEST

    job = make_job(granules=granule_pair, job_type='AUTORIFT', parameters=insar_parameters)
    response = submit_batch(client, batch=[job])
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_float_input(client, tables):
    login(client)
    batch = [make_job(parameters={'resolution': 30.0})]
    setup_requests_mock(batch)
    response = submit_batch(client, batch)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json['jobs'][0]['job_parameters']['resolution'], float)

    batch = [make_job(parameters={'resolution': 30})]
    setup_requests_mock(batch)
    response = submit_batch(client, batch)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json['jobs'][0]['job_parameters']['resolution'], int)


def test_submit_validate_only(client, tables):
    login(client)
    batch = [make_job()]
    setup_requests_mock(batch)

    response = submit_batch(client, batch, validate_only=True)
    assert response.status_code == HTTPStatus.OK
    jobs = tables.jobs_table.scan()['Items']
    assert len(jobs) == 0

    response = submit_batch(client, batch, validate_only=False)
    assert response.status_code == HTTPStatus.OK
    jobs = tables.jobs_table.scan()['Items']
    assert len(jobs) == 1

    response = submit_batch(client, batch, validate_only=None)
    assert response.status_code == HTTPStatus.OK
    jobs = tables.jobs_table.scan()['Items']
    assert len(jobs) == 2
