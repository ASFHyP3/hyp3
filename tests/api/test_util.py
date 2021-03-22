import binascii
import json

import pytest

from hyp3_api import util


def test_serialize_token():
    token = {'foo': 1, 'bar': 2}
    assert util.serialize(token) == 'eyJmb28iOiAxLCAiYmFyIjogMn0='


def test_deserialize_token():
    token = 'eyJmb28iOiAxLCAiYmFyIjogMn0='
    assert util.deserialize(token) == {'foo': 1, 'bar': 2}

    with pytest.raises(util.TokenDeserializeError) as e:
        util.deserialize('foo')
    assert type(e.value.__context__) == binascii.Error
    with pytest.raises(util.TokenDeserializeError) as e:
        util.deserialize('Zm9vbw==')
    assert type(e.value.__context__) == json.JSONDecodeError
    with pytest.raises(util.TokenDeserializeError) as e:
        util.deserialize('fooo')
    assert type(e.value.__context__) == UnicodeDecodeError


def test_token_handlers_invertable():
    token = {'foo': 1, 'bar': 2}
    assert util.deserialize(util.serialize(token)) == token


def test_set_token_url():
    url = util.set_start_token('https://example.com/path?q1=foo&q2=bar', 'start_here')
    assert url == 'https://example.com/path?q1=foo&q2=bar&start_token=start_here'
    url = util.set_start_token(url, 'now_here')
    assert url == 'https://example.com/path?q1=foo&q2=bar&start_token=now_here'
