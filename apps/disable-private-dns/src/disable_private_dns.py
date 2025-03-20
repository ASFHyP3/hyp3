import os
from typing import Any

import boto3


CLIENT = boto3.client('ec2')


def get_endpoint(vpc_id: str, endpoint_name: str) -> dict:
    response = CLIENT.describe_vpc_endpoints()
    endpoints = [endpoint for endpoint in response['VpcEndpoints'] if endpoint['VpcId'] == vpc_id]
    if len(endpoints) == 0:
        raise ValueError(f'No endpoints in VPC {vpc_id}.')

    desired_endpoint = None
    for endpoint in endpoints:
        retrieved_name = [item['Value'] for item in endpoint['Tags'] if item['Key'] == 'Name'][0]
        if retrieved_name == endpoint_name:
            desired_endpoint = endpoint

    if desired_endpoint is None:
        raise ValueError(f'No endpoint in VPC {vpc_id} with name {endpoint_name} exists.')

    return desired_endpoint


def set_private_dns_disabled(endpoint_id: str) -> None:
    response = CLIENT.modify_vpc_endpoint(VpcEndpointId=endpoint_id, PrivateDnsEnabled=False)
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/modify_vpc_endpoint.html
    assert response['Return'] is True, response
    print(f'Private DNS disabled for VPC Endpoint: {endpoint_id}.')


def disable_private_dns(vpc_id: str, endpoint_name: str) -> None:
    endpoint = get_endpoint(vpc_id, endpoint_name)
    if endpoint['PrivateDnsEnabled']:
        print(f'Private DNS enabled for VPC Endpoint: {endpoint["VpcEndpointId"]}, changing...')
        set_private_dns_disabled(endpoint['VpcEndpointId'])
    else:
        print(f'Private DNS already disabled for VPC Endpoint: {endpoint["VpcEndpointId"]}, doing nothing.')


def lambda_handler(event: dict, context: Any) -> None:
    vpc_id = os.environ['VPCID']
    endpoint_name = os.environ['ENDPOINT_NAME']
    print(f'VPC ID {vpc_id}')
    print(f'Endpoint Name: {endpoint_name}')
    disable_private_dns(vpc_id, endpoint_name)
