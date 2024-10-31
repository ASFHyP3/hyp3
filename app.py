import os

import aws_cdk as cdk

from cdk_app.hyp3_stack import HyP3Stack

if __name__ == '__main__':
    app = cdk.App()
    # TODO
    #HyP3Stack(app, os.environ['STACK_NAME'])
    HyP3Stack(app, os.environ['hyp3-cdk'])
    app.synth()
