import os

import aws_cdk as cdk
from aws_cdk import cloudformation_include as cfn_inc
from constructs import Construct


class HyP3Stack(cdk.Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        cfn_inc.CfnInclude(
            scope=self,
            id='Template',
            template_file='packaged.yml',
        )
