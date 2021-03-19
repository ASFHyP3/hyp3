from hyp3_api import util


def test_encode_start_token():
    token = {'foo': 1, 'bar': 2}
    assert util.encode_start_token(token) == 'eyJmb28iOiAxLCAiYmFyIjogMn0='


def test_decode_start_token():
    token = 'eyJmb28iOiAxLCAiYmFyIjogMn0='
    assert util.decode_start_token(token) == {'foo': 1, 'bar': 2}


def test_token_handlers_invertable():
    token = {'foo': 1, 'bar': 2}
    assert util.decode_start_token(util.encode_start_token(token)) == token


def test_build_tokenized_url():
    url = util.set_start_token('https://example.com/path?q1=foo&q2=bar', 'start_here')
    assert url == 'https://example.com/path?q1=foo&q2=bar&start_token=start_here'
