# Deploying HyP3 to JPL

HyP3 can be deployed into a JPL managed AWS commercial account as long as JPL's `roles-as-code`
tooling is provided in the account and in same region as the deployment. Currently, the only
regions supported are `us-west-1`, `us-west-2`, `us-east-1`, and `us-east-2`.

To request `roles-as-code` tooling be deployed in a JPL account, open a 
[Cloud Team Service Desk](https://itsd-jira.jpl.nasa.gov/servicedesk/customer/portal/13) request here:
https://itsd-jira.jpl.nasa.gov/servicedesk/customer/portal/13/create/461?q=roles&q_time=1644889220558


For more information about `roles-as-code`, see:
* https://wiki.jpl.nasa.gov/display/cloudcomputing/IAM+Roles+and+Policies
* https://github.jpl.nasa.gov/cloud/roles-as-code/blob/master/Documentation.md

*Note: you must be on the JPL VPN to view the JPL `.jpl.nasa.gov` links in this document.*

## 1. Roles-as-code

JPL deployment uses a JPL-created service user with a deployment policy attached.
An appropriate deployment policy can be created in a JPL account by deploying the
`hyp3-ci` stack. From the repository root, run:

```shell
aws cloudformation deploy \
    --stack-name hyp3-ci \
    --template-file docs/deployments/JPL-deployment-policy-cf.yml
```

Then open a [Cloud Team Service Desk](https://itsd-jira.jpl.nasa.gov/servicedesk/customer/portal/13)
request for a service user account here:
https://itsd-jira.jpl.nasa.gov/servicedesk/customer/portal/13/create/416?q=service%20user&q_time=1643746791578
with the deployed policy name in the "Managed Permissions to be Attached" field. 
The policy name should look like `hyp3-ci-DeployPolicy-*`, and can be found either
in the [IAM console](https://console.aws.amazon.com/iamv2/home?#/policies) or listed under 
the `hyp3-ci` CloudFormation Stack Resources.   


## 2. Deploy HyP3 to JPL

Once the JPL service user has been created, you should receive a set of AWS Access Keys
which can be used to deploy HyP3 via CI/CD tooling, or manually. 

To deploy HyP3 manually into a JPL account, run these commands from the repository root,
replacing any `<*>` with appropriate values, and adding any other needed parameter
overrides for the deployment:

```shell
export AWS_ACCESS_KEY_ID=<service-user-access-key-id>
export AWS_SECRET_ACCESS_KEY=<service-user-secret-access-key>
export AWS_REGION=<deployment-region>

make files=<supported-job-spec-files> build

aws cloudformation package \
    --template-file apps/main-cf.yml \
    --s3-bucket <template-bucket> \
    --output-template-file packaged.yml

aws cloudformation deploy \
    --stack-name <stack-name> \
    --template-file packaged.yml \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        VpcId=<vpc-ids> \
        SubnetIds=<subnet-ids> \
        EDLUsername=<erthdata-login-username> \
        EDLPassword=<erthdata-login-username> \
        MonthlyJobQuotaPerUser=0
```
