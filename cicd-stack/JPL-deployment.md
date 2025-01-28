# Deploying HyP3 to JPL

This guide walks through steps that are specific to deploying HyP3 into a JPL-managed AWS account.
It should work for any new JPL account and assumes:
* the JPL account setup in the "default" manner by the JPL cloud team
* the developer deploying the account is able to log in with the `power_user` role

## Pre-deployment

*Complete these steps before deploying HyP3.*

### Roles-as-code

JPL restricts developers from creating IAM roles or policies inside their AWS commercial cloud accounts.
However, HyP3 can be deployed into a JPL managed AWS commercial account as long as JPL's `roles-as-code`
tooling is provided in the account and in same region as the deployment. Currently, the only
regions supported are `us-west-1`, `us-west-2`, `us-east-1`, and `us-east-2`.

To request `roles-as-code` tooling be deployed in a JPL account, open a 
[Cloud Team Service Desk](https://itsd-jira.jpl.nasa.gov/servicedesk/customer/portal/13) request here:
https://itsd-jira.jpl.nasa.gov/servicedesk/customer/portal/13/create/461?q=roles&q_time=1644889220558

For more information about `roles-as-code`, see:
* https://wiki.jpl.nasa.gov/display/cloudcomputing/IAM+Roles+and+Policies
* https://github.jpl.nasa.gov/cloud/roles-as-code/blob/master/Documentation.md

*Note: you must be on the JPL VPN to view the JPL `.jpl.nasa.gov` links in this document.*

### Set up a service user

In order to integrate a JPL deployment into our CI/CD pipelines, a JPL-created "service user"
is needed to get long-term (90-day) AWS access keys. When requesting a service user, you'll
need to request an appropriate deployment policy containing all the necessary permissions for
deployment is attached to the user. An appropriate deployment policy can be created in a
JPL account by deploying the `hyp3-ci` stack. From the repository root, run:

```shell
aws cloudformation deploy \
    --stack-name hyp3-ci \
    --template-file cicd-stack/JPL-deployment-policy-cf.yml
```

Then open a [Cloud Team Service Desk](https://itsd-jira.jpl.nasa.gov/servicedesk/customer/portal/13)
request for a service user account here:
https://itsd-jira.jpl.nasa.gov/servicedesk/customer/portal/13/create/416?q=service%20user&q_time=1643746791578
with the deployed policy name in the "Managed Permissions to be Attached" field. 
The policy name should look like `hyp3-ci-DeployPolicy-*`, and can be found either
in the [IAM console](https://console.aws.amazon.com/iamv2/home?#/policies) or listed under 
the `hyp3-ci` CloudFormation Stack Resources.   

Once the JPL service user has been created, you should receive a set of AWS Access Keys
which can be used to deploy HyP3 via CI/CD tooling.

## Post-deployment

*Return to this section after deploying HyP3.*

Because the default state of the JPL account is more restrictive than typically
desired for HyP3, this section describes some additional changes to the account
and HyP3 that may be desired.

### Allow a public HyP3 content bucket

By default, JPL commercial AWS accounts have an S3 account level Block All Public
Access set which must be disabled by the JPL Cloud team in order to attach a public
bucket policy to the HyP3 content bucket.

The steps to disable the account level Block All Public Access setting is outlined
in the S3 section here:
https://wiki.jpl.nasa.gov/display/cloudcomputing/AWS+Service+Policies+at+JPL

Once this setting has been disabled, you can attach a public bucket policy to the
HyP3 content bucket by redeploying HyP3 using the `JPL-public` security environment.
