import os

import aws_cdk as cdk
from aws_cdk import cloudformation_include as cfn_inc
from constructs import Construct


class HyP3Stack(cdk.Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        params = {
            'VpcId': os.environ['VPC_ID'],
            'SubnetIds': os.environ['SUBNET_IDS'].split(','),
            'SecretArn': os.environ['SECRET_ARN'],
            'ImageTag': os.environ['IMAGE_TAG'],
            'ProductLifetimeInDays': os.environ['PRODUCT_LIFETIME'],
            'AuthPublicKey': os.environ['AUTH_PUBLIC_KEY'],
            'DefaultCreditsPerUser': os.environ['DEFAULT_CREDITS_PER_USER'],
            'DefaultApplicationStatus': os.environ['DEFAULT_APPLICATION_STATUS'],
            'DefaultMaxvCpus': os.environ['DEFAULT_MAX_VCPUS'],
            'ExpandedMaxvCpus': os.environ['EXPANDED_MAX_VCPUS'],
            'MonthlyBudget': os.environ['MONTHLY_BUDGET'],
            'RequiredSurplus': os.environ['REQUIRED_SURPLUS'],
            'AmiId': os.environ['AMI_ID'],
            'InstanceTypes': os.environ['INSTANCE_TYPES'],
        }
        if os.environ['SECURITY_ENVIRONMENT'] != 'EDC':
            params['DomainName'] = os.environ['DOMAIN_NAME']
            params['CertificateArn'] = os.environ['CERTIFICATE_ARN']
        else:
            params['OriginAccessIdentityId'] = os.environ['ORIGIN_ACCESS_IDENTITY_ID']
            params['DistributionUrl'] = os.environ['DISTRIBUTION_URL']

        template = cfn_inc.CfnInclude(
            scope=self,
            id='Template',
            template_file='packaged.yml',
            parameters=params,
        )
