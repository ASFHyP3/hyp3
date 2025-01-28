# Deploying HyP3 to ASF

These are steps that are specific to deploying HyP3 into an ASF-managed AWS account.

## Pre-deployment

*Complete these steps before deploying HyP3.*

### Set up a CloudFormation templates bucket

*Note: This section only needs to be completed once per AWS account.*

A new account will not have a bucket for storing AWS CloudFormation templates,
which is needed to deploy a CloudFormation stack. AWS will automatically make a
suitable bucket if you try and create a new CloudFormation Stack in the AWS Console:
* navigating to the CloudFormation service in the region you are going to deploy to
* Click the orange "Create stack" button 
* On the create stack screen
  * For "Prepare template" make select "Template is ready"
  * For "Template source" select "Upload a template file"
  * Choose any JSON or YAML formatted file from your computer to upload
  * Once the file is uploaded, you should see an S3 URL on the bottom indicating the
    bucket the template file was uploaded. This is your newly created CloudFormation
    templates bucket and should be named something like `cf-templates-<HASH>-<region>`
  * Click "Cancel" to exit the CloudFormation stack creation now that we have a
    templates bucket

### Deploy CICD stack

*Note: This stack should only be deployed once per AWS account. This stack also
assumes you are only deploying into a single AWS Region. If you are deploying into
multiple regions in the same AWS account, you'll need to adjust the IAM permissions
that are limited to a single region.*

In order to integrate an ASF deployment we'll need:

1. Set the account-wide API Gateway logging permissions
2. A deployment role with the necessary permissions to deploy HyP3
3. A "service user" so that we can generate long-term AWS access keys and
   integrate the deployment into our CI/CD pipelines

These can be done by deploying the `hyp3-ci` stack.
From the repository root, run the following command, replacing `<profile>` and `<template-bucket>`
with the appropriate values for your AWS account:

```shell
aws --profile <profile> cloudformation deploy \
    --stack-name hyp3-ci \
    --template-file docs/deployments/ASF-deployment-ci-cf.yml \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides TemplateBucketName=<template-bucket>
```

Once the `github-actions` IAM user has been created, you can create a set of AWS
Access Keys for that user, which can be used to deploy HyP3 via CI/CD tooling. 

Go to AWS console -> IAM -> Users -> github-actions -> security credentials tab -> "create access key".
Store the access key ID and secret access key using your team's password manager.
