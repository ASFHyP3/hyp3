# HyP3
![Static code analysis](https://github.com/ASFHyP3/hyp3/workflows/Static%20code%20analysis/badge.svg)
![Deploy to AWS](https://github.com/ASFHyP3/hyp3/workflows/Deploy%20to%20AWS/badge.svg)
![Run tests](https://github.com/ASFHyP3/hyp3/workflows/Run%20tests/badge.svg)

[![DOI](https://zenodo.org/badge/259996151.svg)](https://zenodo.org/badge/latestdoi/259996151)


A processing environment for HyP3 Plugins in AWS.

## Developer Setup

1. Clone the repository
   ```
   git clone git@github.com:ASFHyP3/hyp3.git
   cd hyp3
   ```
2. Create and activate a conda environment
   ```
   conda env create -f environment.yml
   conda activate hyp3
   ```
3. Run the tests:
   ```
   make tests
   ```
   Alternatively, you can invoke `pytest` directly (e.g. for passing command-line arguments):
   ```
   eval $(make env)
   make render && pytest
   ```
   In particular, to skip tests that require a network connection, run:
   ```
   pytest -m 'not network'
   ```
   And to run *only* those tests:
   ```
   pytest -m network
   ```
   When writing new tests, decorate such tests with `@pytest.mark.network`.

   Also, remember to re-run `make render` after making changes to rendered files.

## Deployment

### Security environments

We currently have HyP3 deployments in various AWS accounts managed by three different organizations,
also referred to as "security environments" throughout our code and docs
(because the AWS accounts have different security requirements depending on the organization):
- ASF
- JPL
- EDC (Earthdata Cloud)

EDC deployment steps are not fully documented here.
ASF and JPL deployment steps should be complete, so let us know if something is missing!

For JPL, these deployment docs assume that:
- the JPL account was setup in the "default" manner by the JPL cloud team
- the developer deploying the account is able to log in with the `power_user` role

For a new EDC deployment, you need the following items (not necessarily a comprehensive list):
- SSL certificate in AWS Certificate Manager for custom CloudFront domain name
- ID of the CloudFront Origin Access Identity used to access data in S3

### Set up a CloudFormation templates bucket

TODO: Does this section apply to EDC?

*Security environment(s): ASF*

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

### Deploy CICD stack for ASF accounts

*Security environment(s): ASF*

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
    --template-file cicd-stacks/ASF-deployment-ci-cf.yml \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides TemplateBucketName=<template-bucket>
```

Once the `github-actions` IAM user has been created, you can create a set of AWS
Access Keys for that user, which can be used to deploy HyP3 via CI/CD tooling.

Go to AWS console -> IAM -> Users -> github-actions -> security credentials tab -> "create access key".
Store the access key ID and secret access key using your team's password manager.

### Roles-as-code for JPL accounts

*Security environment(s): JPL*

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

### Set up a service user for JPL accounts

*Security environment(s): JPL*

In order to integrate a JPL deployment into our CI/CD pipelines, a JPL-created "service user"
is needed to get long-term (90-day) AWS access keys. When requesting a service user, you'll
need to request an appropriate deployment policy containing all the necessary permissions for
deployment is attached to the user. An appropriate deployment policy can be created in a
JPL account by deploying the `hyp3-ci` stack. From the repository root, run:

```shell
aws cloudformation deploy \
    --stack-name hyp3-ci \
    --template-file cicd-stacks/JPL-deployment-policy-cf.yml
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

### Create Earthdata Login user

*Security environment(s): ASF, JPL, EDC*

Assuming the job spec(s) for your chosen job type(s) require the `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` secrets,
you will need to create an Earthdata Login user for your deployment if you do not already have one:

1. Visit https://urs.earthdata.nasa.gov/home and click "Register"
2. Fill in the required fields
3. Fill in a Study Area
4. After finishing, visit Eulas -> Accept New EULAs and accept "Alaska Satellite Facility Data Access"
5. Log into Vertex as the new user, and confirm you can download files, e.g. https://datapool.asf.alaska.edu/METADATA_SLC/SA/S1A_IW_SLC__1SDV_20230130T184017_20230130T184044_047017_05A3C3_381F.iso.xml
6. Add the new username and password to your team's password manager.

### Create secret with AWS Secrets Manager

*Security environment(s): ASF, JPL, EDC*

Go to AWS console -> Secrets Manager, then:
- Click the orange "Store a new secret" button
- On the create secret screen:
  - For "Secret Type" select "Other type of secret"
  - Enter all required secret key-value pairs. Notably, the keys should be the secret names as listed (case-sensitive)
    in the [job specs](./job_spec/) that will be deployed
  - Click the orange "Next" button
  - Give the secret the same name that you plan to give to the HyP3 CloudFormation stack when you deploy it (below)
  - Click the orange "Next" button
  - Click the orange "Next" button (we won't configure rotation)
  - Click the orange "Store" button to save the Secret

### Upload SSL cert

TODO: Does this section apply to JPL?

*Security environment(s): ASF*

Upload the `*.asf.alaska.edu` SSL certificate to AWS ACM.

AWS console -> certificate manager (ACM) -> import certificate

Open https://gitlab.asf.alaska.edu/operations/puppet/-/tree/production/site/modules/certificates/files
- The contents of the `asf.alaska.edu.cer` file go in Certificate body
- The contents of the `asf.alaska.edu.key` file go in Certificate private key
- The contents of the `incommon.cer` file goes in Certificate chain

### Create the GitHub environment

*Security environment(s): ASF, JPL, EDC*

1. Go to https://github.com/ASFHyP3/hyp3/settings/environments -> New Environment
2. Check "required reviewers" and add the appropriate team(s) or user(s)
3. Change "Deployment branches" to "protected branches"
4. Add the following environment secrets:
    - `AWS_REGION` - e.g. `us-west-2`
    - `CLOUDFORMATION_ROLE_ARN` - part of the ASF (not JPL) CI/CD stack that you deployed, e.g. `arn:aws:iam::xxxxxxxxxxxx:role/hyp3-ci-CloudformationDeploymentRole-XXXXXXXXXXXXX`
    - `SECRET_ARN` - ARN for the AWS Secrets Manager Secret that you created manually
    - `V2_AWS_ACCESS_KEY_ID` - Access key ID that you created for the `github-actions` user
    - `V2_AWS_SECRET_ACCESS_KEY` - Secret access key that you created for the `github-actions` user
    - `VPC_ID` - ID of the default VPC for this AWS account and region (aws console -> vpc -> your VPCs, e.g. `vpc-xxxxxxxxxxxxxxxxx`)
    - `SUBNET_IDS` - Comma delimited list (no spaces) of the default subnets for this VPC (aws console -> vpc -> subnets, e.g. `subnet-xxxxxxxxxxxxxxxxx,subnet-xxxxxxxxxxxxxxxxx,subnet-xxxxxxxxxxxxxxxxx,subnet-xxxxxxxxxxxxxxxxx`)
    - `CERTIFICATE_ARN` - ARN of the AWS Certificate Manager certificate that you imported manually (aws console -> certificate manager -> list certificates, e.g. `arn:aws:acm:us-west-2:xxxxxxxxxxxx:certificate/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

### Create the HyP3 deployment

*Security environment(s): ASF, JPL, EDC*

You will need to create a GitHub Actions workflow for the deployment.

For non-EDC, non-JPL deployments, you can copy the
[deploy-enterprise-test.yml](.github/workflows/deploy-enterprise-test.yml) workflow
and delete the extra environments.
Then update all of the fields (`environment`, `domain`, `template_bucket`, etc.) as appropriate for your deployment.
Also make sure to update the top-level `name` of the workflow and the name of the branch to deploy from.
(This is typically `main` for prod deployments, `develop` for test deployments, or a feature branch name for sandbox deployments.)

The deployment workflow will run as soon as you merge your changes into the branch specified in the workflow file.
Wait for the CloudFormation stack to finish being created in your AWS account.

TODO:
- Should we create some kind of template workflow file?
- Enterprise deployments are currently in `deploy-enterprise.yml`, but we might be splitting them up by team?

### Allow a public HyP3 content bucket for JPL accounts

*Security environment(s): JPL*

By default, JPL commercial AWS accounts have an S3 account level Block All Public
Access set which must be disabled by the JPL Cloud team in order to attach a public
bucket policy to the HyP3 content bucket.

The steps to disable the account level Block All Public Access setting is outlined
in the S3 section here:
https://wiki.jpl.nasa.gov/display/cloudcomputing/AWS+Service+Policies+at+JPL

Once this setting has been disabled, you can attach a public bucket policy to the
HyP3 content bucket by redeploying HyP3 using the `JPL-public` security environment.

### Grant AWS account permission to pull the hyp3-gamma container

*Security environment(s): ASF, EDC*

If your HyP3 deployment uses the `RTC_GAMMA` or `INSAR_GAMMA` job types
and is the first such deployment in this AWS account,
you will need to grant the AWS account permission to pull the `hyp3-gamma` container.

In the **HyP3 AWS account** (not the AWS account for the new deployment),
go to AWS console -> Elastic Container Registry -> hyp3-gamma -> Permissions -> "Edit policy JSON":
1. Add the new AWS account root user to the `Principal` (e.g. `arn:aws:iam::xxxxxxxxxxxx:root`)
2. Update list of account names in the `SID`

### Create DNS record for new HyP3 API

*Security environment(s): ASF, JPL*

Open a PR adding a line to https://gitlab.asf.alaska.edu/operations/puppet/-/blob/production/modules/legacy_dns/files/asf.alaska.edu.db
for the new custom domain name (AWS console -> api gateway -> custom domain names -> "API Gateway domain name").

Ask the Platform team in the `~development-support` channel in Mattermost to review/merge the PR.

Changes should take effect within 15-60 minutes after merging.
Confirm that a Swagger UI is available at your chosen API URL.

Update the [AWS Accounts and HyP3 Deployments](https://docs.google.com/spreadsheets/d/1gHxgVbgQbqFNMQQe042Ku5L2pM6LLTOBDOFgO1FgZeU/) spreadsheet.

## Running the API Locally

The API can be run locally to verify changes, but must be connected to a set of existing DynamoDB tables.

1. Set up AWS credentials in your environment as described
   [here](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration).
   Also see our [wiki page](https://github.com/ASFHyP3/.github-private/wiki/AWS-Access#aws-access-keys).
2. Edit `tests/cfg.env` to specify the names of existing DynamoDB tables from a particular HyP3 deployment.
   Delete all of the `AWS_*` variables.
3. Run the API (replace `<profile>` with the AWS config profile that corresponds to the HyP3 deployment):
   ```sh
   AWS_PROFILE=<profile> make run
   ```
4. You should see something like `Running on http://127.0.0.1:8080` in the output. Open the host URL in your browser.
   You should see the Swagger UI for the locally running API.
5. In Chrome or Chromium, from the Swagger UI tab, open Developer tools, select the Application tab, then select
   the host URL under Cookies. In Firefox, open Web Developer Tools, select the Storage tab, then select
   the host URL under Cookies. Add a new cookie with the following Name:
   ```
   asf-urs
   ```
   And the following Value:
   ```
   eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1cnMtdXNlci1pZCI6InVzZXIiLCJleHAiOjIxNTk1Mzc0OTYyLCJ1cnMtZ3JvdXBzIjpbeyJuYW1lIjoiYXV0aC1ncm91cCIsImFwcF91aWQiOiJhdXRoLXVpZCJ9XX0.hMtgDTqS5wxDPCzK9MlXB-3j6MAcGYeSZjGf4SYvq9Y
   ```
   And `/` for Path.
6. To verify access, query the `GET /user` endpoint and verify that the response includes `"user_id": "user"`.
