import flask

from hyp3_api import handlers


def test_build_next_token():
    token = {'foo': 1, 'bar': 2}
    assert handlers.build_next_token(token) == 'eyJmb28iOiAxLCAiYmFyIjogMn0='


def test_decode_start_token():
    token = 'eyJmb28iOiAxLCAiYmFyIjogMn0='
    assert handlers.decode_start_token(token) == {'foo': 1, 'bar': 2}


def test_token_handlers_invertable():
    token = {'foo': 1, 'bar': 2}
    assert handlers.decode_start_token(handlers.build_next_token(token)) == token


def test_build_tokenized_url():
    with handlers.connexion_app.app.test_request_context('/jobs'):
        flask.request.url = 'https://example.com/path?q1=foo&q2=bar'
        url = handlers.build_tokenized_url('start_here')
        assert url == 'https://example.com/path?q1=foo&q2=bar&start_token=start_here'
