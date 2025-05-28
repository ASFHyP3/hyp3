import datetime
import decimal

import pytest
from boto3.dynamodb.conditions import Key

import dynamo


def test_get_request_time_expression():
    response = dynamo.util.get_request_time_expression('2021-01-01T00:00:00+00:00', '2021-01-02T00:00:00+00:00')
    assert response == Key('request_time').between('2021-01-01T00:00:00+00:00', '2021-01-02T00:00:00+00:00')

    response = dynamo.util.get_request_time_expression('2021-01-01T00:00:00+00:00', None)
    assert response == Key('request_time').gte('2021-01-01T00:00:00+00:00')

    response = dynamo.util.get_request_time_expression(None, '2021-01-02T00:00:00+00:00')
    assert response == Key('request_time').lte('2021-01-02T00:00:00+00:00')

    response = dynamo.util.get_request_time_expression(None, None)
    assert response is None


def test_format_time():
    date = datetime.datetime(2021, 2, 3, 4, 5, 6, 7, tzinfo=datetime.UTC)
    assert dynamo.util.format_time(date) == '2021-02-03T04:05:06+00:00'

    offset = datetime.timedelta(hours=1)
    date = datetime.datetime(2022, 3, 4, 5, 6, 7, 8, tzinfo=datetime.timezone(offset))
    assert dynamo.util.format_time(date) == '2022-03-04T04:06:07+00:00'

    date = datetime.datetime(2021, 2, 3, 4, 5, 6, 7)
    with pytest.raises(ValueError):
        dynamo.util.format_time(date)


def test_convert_floats_to_decimals():
    payload = [
        {
            'a': [123, 123.45],
            'b': {},
            'c': '123.45',
            'd': 123,
            'e': 123.45,
        },
        '123.45',
        123,
        123.45,
    ]

    response = dynamo.util.convert_floats_to_decimals(payload)
    assert response == [
        {
            'a': [123, decimal.Decimal('123.45')],
            'b': {},
            'c': '123.45',
            'd': 123,
            'e': decimal.Decimal('123.45'),
        },
        '123.45',
        123,
        decimal.Decimal('123.45'),
    ]


def test_convert_decimals_to_numbers():
    payload = [
        {
            'a': [123, decimal.Decimal(123.45)],
            'b': {},
            'c': '123.45',
            'd': 123,
            'e': decimal.Decimal(123.45),
        },
        '123.45',
        decimal.Decimal('123'),
        123.45,
    ]

    response = dynamo.util.convert_decimals_to_numbers(payload)
    assert response == [
        {
            'a': [123, 123.45],
            'b': {},
            'c': '123.45',
            'd': 123,
            'e': 123.45,
        },
        '123.45',
        123,
        123.45,
    ]
