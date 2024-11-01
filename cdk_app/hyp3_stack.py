import aws_cdk as cdk
from aws_cdk import cloudformation_include as cfn_inc
from constructs import Construct


class HyP3Stack(cdk.Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        main_template = cfn_inc.CfnInclude(
            scope=self,
            id='MainStack',
            template_file='packaged.yml',
        )

        # TODO: this isn't needed, but is an example of getting an output from a nested stack
        cluster_template = main_template.load_nested_stack(
            'Cluster',
            template_file='apps/compute-cf.yml'
        ).included_template
        print(cluster_template.get_output('JobQueueArn'))
