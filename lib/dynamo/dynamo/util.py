from datetime import UTC, datetime
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from dateutil.parser import parse


DYNAMODB_RESOURCE = boto3.resource('dynamodb')


def get_request_time_expression(start, end):
    key = Key('request_time')
    formatted_start = format_time(parse(start)) if start else None
    formatted_end = format_time(parse(end)) if end else None

    if formatted_start and formatted_end:
        return key.between(formatted_start, formatted_end)
    if formatted_start:
        return key.gte(formatted_start)
    if formatted_end:
        return key.lte(formatted_end)


def format_time(time: datetime) -> str:
    if time.tzinfo is None:
        raise ValueError(f'missing tzinfo for datetime {time}')
    utc_time = time.astimezone(UTC)
    return utc_time.isoformat(timespec='seconds')


def current_utc_time() -> str:
    return format_time(datetime.now(UTC))


def convert_floats_to_decimals(element):
    if type(element) is float:
        return Decimal(str(element))
    if type(element) is list:
        return [convert_floats_to_decimals(item) for item in element]
    if type(element) is dict:
        return {key: convert_floats_to_decimals(value) for key, value in element.items()}
    return element


def convert_decimals_to_numbers(element):
    if type(element) is Decimal:
        as_float = float(element)
        if as_float.is_integer():
            return int(as_float)
        return as_float
    if type(element) is list:
        return [convert_decimals_to_numbers(item) for item in element]
    if type(element) is dict:
        return {key: convert_decimals_to_numbers(value) for key, value in element.items()}
    return element
