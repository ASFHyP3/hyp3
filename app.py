import os

import aws_cdk as cdk

from cdk_app.hyp3_stack import HyP3Stack

if __name__ == '__main__':
    app = cdk.App()
    HyP3Stack(app, os.environ['STACK_NAME'])
    app.synth()
