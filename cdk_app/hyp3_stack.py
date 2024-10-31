import os

import aws_cdk as cdk
from aws_cdk import cloudformation_include as cfn_inc
from constructs import Construct


class HyP3Stack(cdk.Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        template = cfn_inc.CfnInclude(
            scope=self,
            id='Template',
            template_file='packaged.yml',
            parameters={
                'VpcId': os.environ['VPC_ID'],
                'SubnetIds': os.environ['SUBNET_IDS'],
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
                # non-EDC only:
                'DomainName': os.getenv('DOMAIN_NAME', ''),
                'CertificateArn': os.getenv('CERTIFICATE_ARN', ''),
                # EDC only:
                'OriginAccessIdentityId': os.getenv('ORIGIN_ACCESS_IDENTITY_ID', ''),
                'DistributionUrl': os.getenv('DISTRIBUTION_URL', ''),
            }
        )
