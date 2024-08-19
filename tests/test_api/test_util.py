import binascii
import json

import pytest

from hyp3_api import util


def test_get_granules():
    assert util.get_granules(
        [
            {'job_parameters': {'granules': []}},
            {'job_parameters': {'granules': ['A']}},
            {'job_parameters': {'granules': ['B']}},
            {'job_parameters': {'granules': ['C', 'D']}},
            {'job_parameters': {'granules': ['C', 'D', 'E']}},
            {'job_parameters': {'granules': ['F', 'F']}},
            {'job_parameters': {}},
        ]
    ) == set({'A', 'B', 'C', 'D', 'E', 'F'})


def test_serialize_token():
    token = {'foo': 1, 'bar': 2}
    assert util.serialize(token) == 'eyJmb28iOiAxLCAiYmFyIjogMn0='


def test_deserialize_token():
    token = 'eyJmb28iOiAxLCAiYmFyIjogMn0='
    assert util.deserialize(token) == {'foo': 1, 'bar': 2}

    with pytest.raises(util.TokenDeserializeError) as e:
        util.deserialize('foo')
    assert type(e.value.__context__) is binascii.Error

    with pytest.raises(util.TokenDeserializeError) as e:
        util.deserialize('Zm9vbw==')
    assert type(e.value.__context__) is json.JSONDecodeError

    with pytest.raises(util.TokenDeserializeError) as e:
        util.deserialize('fooo')
    assert type(e.value.__context__) is UnicodeDecodeError


def test_token_handlers_invertable():
    token = {'foo': 1, 'bar': 2}
    assert util.deserialize(util.serialize(token)) == token


def test_build_next_url():
    url = util.build_next_url('https://example.com/path?q1=foo&q2=bar', 'start_here')
    assert url == 'https://example.com/path?q1=foo&q2=bar&start_token=start_here'

    url = util.build_next_url(url, 'now_here')
    assert url == 'https://example.com/path?q1=foo&q2=bar&start_token=now_here'

    url = util.build_next_url('https://example.com/path?q1=foo&q2=bar', 'NEXT', x_forwarded_host='new-domain.edu')
    assert url == 'https://new-domain.edu/path?q1=foo&q2=bar&start_token=NEXT'

    url = util.build_next_url('https://example.com:443/path?q1=foo&q2=bar', 'NEXT', x_forwarded_host='new-domain.edu')
    assert url == 'https://new-domain.edu/path?q1=foo&q2=bar&start_token=NEXT'

    url = util.build_next_url('https://example.com/root/path?q1=foo&q2=bar', 'NEXT')
    assert url == 'https://example.com/root/path?q1=foo&q2=bar&start_token=NEXT'

    url = util.build_next_url('https://example.com/root/path?q1=foo&q2=bar', 'NEXT', root_path='/root')
    assert url == 'https://example.com/path?q1=foo&q2=bar&start_token=NEXT'
