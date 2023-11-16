import boto3


CLIENT = boto3.client('ec2')


def get_endpoint(endpoint_name):
    response = CLIENT.describe_vpc_endpoints()
    for endpoint in response['VpcEndpoints']:
        retrieved_name = [item['Value'] for item in endpoint['Tags'] if item['Key'] == 'Name'][0]
        if retrieved_name == endpoint_name:
            return endpoint


def set_private_dns_disabled(endpoint_id):
    response = CLIENT.modify_vpc_endpoint(VpcEndpointId=endpoint_id, PrivateDnsEnabled=False)
    print(f"Private DNS disabled for VPC Endpoint: {endpoint_id}.")
    return response


def enable_private_dns(endpoint_name):
    endpoint = get_endpoint(endpoint_name)
    if not endpoint['PrivateDnsEnabled']:
        print(f"Private DNS enabled for VPC Endpoint: {endpoint['VpcEndpointId']}, changing...")
        set_private_dns_disabled(endpoint['VpcEndpointId'])
    else:
        print(f"Private already disabled for VPC Endpoint: {endpoint['VpcEndpointId']}, doing nothing.")


def lambda_handler(event, context):
    print('## EVENT')
    print(event)
    print('## PROCESS BEGIN...')
    name = 'VPC Endpoint - Consumer'
    enable_private_dns(name)
    print('## PROCESS COMPLETE!')
