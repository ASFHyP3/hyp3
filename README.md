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

### Why would you set up a hyp3 deployment?

A HyP3 deployment stack provides a reproducible cloud processing environment that bundles AWS infrastructure, execution logic, and cost controls, enabling scalable, on-demand computation with clear operational costs.

> [!IMPORTANT]
> It's not currently possible to deploy HyP3 fully independent of ASF due to our integration with 
> [ASF Vertex](https://search.alaska.edu). If you'd like your own deployment of HyP3, please open an issue here or
> email our User Support Office at [uso@asf.alaska.edu](mailto:uso@asf.alaska.edu?subject=Custom%20HyP3%20Deployment)
> with your request. 

### Security environments

We currently have HyP3 deployments in various AWS accounts managed by three different organizations,
also referred to as "security environments" throughout our code and docs
(because the AWS accounts have different security requirements depending on the organization):
- ASF
- EDC (Earthdata Cloud)
- JPL
- JPL-public 

For EDC, you will also need to refer to our
[Deploy HyP3 to Earthdata Cloud](https://github.com/ASFHyP3/.github-private/blob/main/docs/Deploy-HyP3-to-Earthdata-Cloud.md)
internal docs article (only accessible to members of ASF).

> [!IMPORTANT]
> JPL deployments _must_ start with the JPL security environment, but can be migrated to `JPL-public`
> after they are fully deployed and approved to have a public bucket.

For JPL, these deployment docs assume that:
- the JPL account was set up in the "default" manner by the JPL cloud team
- the developer deploying the account is able to log in with the `power_user` role

> [!TIP]
> You can expand and collapse details specific to a security environment as you go through this README.
> Make sure you're looking at the details for the security environment you're deploying into!  

### Set up 

#### Ensure there is a CloudFormation templates bucket

In order to deploy HyP3, the AWS account will need an S3 bucket to store AWS CloudFormation
templates in the same region as the deployment. 

For JPL and EDC security environments, this will likely have already been set up for you by their 
respective cloud services team. You can confirm this by going to the AWS S3 console and looking 
for a bucket named something like `cf-templates-<HASH>-<region>`. If not, follow the ASF steps below.

<details>
<summary>ASF: Create a CloudFormation templates bucket</summary>
<br />

*Note: This section only needs to be completed once per region used in an AWS account.*

A new account will not have a bucket for storing AWS CloudFormation templates,
which is needed to deploy a CloudFormation stack. AWS will automatically make a
suitable bucket if you try and create a new CloudFormation Stack in the AWS Console:

1. Navigate to the CloudFormation service in the region you are going to deploy to
1. Click the orange "Create stack" button
1. For "Prepare template" make select "Template is ready"
1. For "Template source" select "Upload a template file"
1. Choose any JSON or YAML formatted file from your computer to upload
1. Once the file is uploaded, you should see an S3 URL on the bottom indicating the
   bucket the template file was uploaded. This is your newly created CloudFormation
   templates bucket and should be named something like `cf-templates-<HASH>-<region>`
1. Click "Cancel" to exit the CloudFormation stack creation now that we have a templates bucket

</details>

#### Enable CI/CD

The primary and recommended way to deploy HyP3 is though our GitHub Actions CI/CD pipeline.
For ASF and JPL, this requires some setup:

<details>
<summary>ASF: Create a service user and deployment role</summary>
<br />

In order to integrate an ASF deployment we'll need:

1. Account-wide API Gateway logging permissions
2. A deployment role with the necessary permissions to deploy HyP3
3. A "service user" so that we can generate long-term AWS access keys and
   integrate the deployment into our CI/CD pipelines

These can be done by deploying the [ASF CI stack](cicd-stacks/ASF-deployment-ci-cf.yml).

*Warning: This stack only needs to be deployed once per AWS account. This stack also
assumes you are only deploying into a single AWS Region. If you are deploying into
multiple regions in the same AWS account, you'll need to adjust the IAM permissions
that are limited to a single region.*

From the repository root, run the following command, replacing `<profile>` and `<template-bucket>`
with the appropriate values for your AWS account:

```shell
aws --profile <profile> cloudformation deploy \
    --stack-name hyp3-ci \
    --template-file cicd-stacks/ASF-deployment-ci-cf.yml \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides TemplateBucketName=<template-bucket>
```

Once the `github-actions` IAM user has been created, you can create an AWS access key for that user,
which we will use to deploy HyP3 via CI/CD tooling:

1. Go to AWS console -> IAM -> Users -> github-actions -> security credentials tab -> "create access key".
2. Select "Other" for key usage
3. (Optional)Add tag value to describe the key, such as "For GitHub Actions CI/CD pipelines"
4. Store the access key ID and secret access key using your team's password manager. You will use them below in "Create the GitHub environment"
   as `V2_AWS_ACCESS_KEY_ID` and `V2_AWS_SECRET_ACCESS_KEY`.
</details>

<details>
<summary>JPL: Set up roles-as-code and request a service user</summary>

##### Roles-as-code for JPL accounts

JPL restricts developers from creating IAM roles or policies inside their AWS commercial cloud accounts.
However, HyP3 can be deployed into a JPL managed AWS commercial account as long as JPL's `roles-as-code`
tooling is provided in the account and in the same region as the deployment. Currently, the only
regions supported are `us-west-1`, `us-west-2`, `us-east-1`, and `us-east-2`.

To request `roles-as-code` tooling be deployed in a JPL account, open a
[Cloud Team Service Desk](https://itsd-jira.jpl.nasa.gov/servicedesk/customer/portal/13) request here:
https://itsd-jira.jpl.nasa.gov/servicedesk/customer/portal/13/create/461?q=roles&q_time=1644889220558

For more information about `roles-as-code`, see:
* https://wiki.jpl.nasa.gov/display/cloudcomputing/IAM+Roles+and+Policies
* https://github.jpl.nasa.gov/cloud/roles-as-code/blob/master/Documentation.md

*Note: You must be on the JPL VPN to view the `.jpl.nasa.gov` links in this document.*

##### Set up a service user for JPL accounts

In order to integrate a JPL deployment into our CI/CD pipelines, a JPL-created "service user"
is needed to get long-term (90-day) AWS access keys. When requesting a service user, you'll
need to request that an appropriate deployment policy containing all the necessary permissions for
deployment is attached to the user. An appropriate deployment policy can be created in a
JPL account by deploying the [JPL CI stack](cicd-stacks/JPL-deployment-policy-cf.yml). 

From the repository root, run:
```shell
aws cloudformation deploy \
    --stack-name hyp3-ci \
    --template-file cicd-stacks/JPL-deployment-policy-cf.yml
```

*Warning: This stack should only be deployed once per AWS account. This stack also
assumes you are only deploying into a single AWS Region. If you are deploying into
multiple regions in the same AWS account, you'll need to adjust the IAM permissions
that are limited to a single region.*

Then open a [Cloud Team Service Desk](https://itsd-jira.jpl.nasa.gov/servicedesk/customer/portal/13)
request for a service user account here:
https://itsd-jira.jpl.nasa.gov/servicedesk/customer/portal/13/create/416?q=service%20user&q_time=1643746791578
with the deployed policy name in the "Managed Permissions to be Attached" field.
The policy name should look like `hyp3-ci-DeployPolicy-*`, and can be found either
in the [IAM console](https://console.aws.amazon.com/iamv2/home?#/policies) or listed under
the `hyp3-ci` CloudFormation Stack Resources.

Once the JPL service user has been created, you should receive an AWS access key
which can be used to deploy HyP3 via CI/CD tooling.

*Important: These keys will be stored in the associated JPL-managed AWS account in an AWS SecretsManager secret
with the same name as the service user. JPL automatically rotates them every 90 days and so
will need to be periodically refreshed in the GitHub deploy environment secrets (described below).*

</details>

#### Create Earthdata Login user

Assuming the job spec(s) for your chosen job type(s) require the `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` secrets,
you will need to create an Earthdata Login user for your deployment if you do not already have one:

1. Visit https://urs.earthdata.nasa.gov/home and click "Register"
2. Fill in the required fields
3. Fill in a Study Area
4. After finishing, visit Eulas -> Accept New EULAs and accept "Alaska Satellite Facility Data Access"
5. Log into Vertex as the new user, and confirm you can download files, e.g. https://datapool.asf.alaska.edu/METADATA_SLC/SA/S1A_IW_SLC__1SDV_20230130T184017_20230130T184044_047017_05A3C3_381F.iso.xml
6. Add the new username and password to your team's password manager.

#### Create secret with AWS Secrets Manager

Go to AWS console -> Secrets Manager, then:

1. Click the orange "Store a new secret" button
2. For "Secret Type" select "Other type of secret"
3. Enter all required secret key-value pairs. Notably, the keys should be the secret names as listed (case-sensitive) in the [job specs](./job_spec/) that will be deployed
4. Click the orange "Next" button
5. Give the secret the same name that you plan to give to the HyP3 CloudFormation stack when you deploy it (below)
6. Click the orange "Next" button
7. Click the orange "Next" button (we won't configure rotation)
8. Click the orange "Store" button to save the Secret

#### Request SSL cert

*Note: For EDC accounts, you should create the cert in the `us-east-1` region
for use with the CloudFront distribution that you will create later,
even if you're deploying HyP3 to `us-west-2`.*

To allow HTTPS connections, HyP3 needs an SSL certificate that is valid for its deployment domain name (URL):

AWS console -> AWS Certificate Manager -> Request certificate:\
1. Select "Request a public certificate"
2. Click the orange "Next" button
3. Choose a "Fully qualified domain name". Domain name should be something like `hyp3-foobar.asf.alaska.edu` or for a test deployment `hyp3-foobar-test.asf.alaska.edu`.
3. Choose "DNS validation"
4. Copy the "CNAME name" and "CNAME value"

Then copy past the add the validation record to a row of
https://gitlab.asf.alaska.edu/operations/puppet/-/edit/production/modules/legacy_dns/files/asf.alaska.edu.db
in the format `<CNAME_name> in CNAME <CNAME_value>.`  (see previous records for examples).

### Create the GitHub environment

> [!WARNING]
> This step must be done by someone with admin access to the [ASFHyP3/hyp3](https://github.com/ASFHyP3/hyp3)
> repository, which is generally only possible for ASF employees on HyP3 development teams.

1. Go to https://github.com/ASFHyP3/hyp3/settings/environments -> New Environment
2. Name the environment like your chosen domain name i.e. `hyp3-foobar` or `hyp3-foobar-test`
3. Check "required reviewers" and add the appropriate team(s) or user(s)
4. Change "Deployment branches and tags" to "Selected branches and tags" and
   - add a deployment branch or tag rule
   - use "Ref Type: Branch" and write the name of the branch it will be deploying out of.
     (This is typically `main` for prod deployments, `develop` for test deployments, or a feature branch name for sandbox deployments.)
5. Add the following environment secrets:
    - `AWS_REGION` - e.g. `us-west-2`
    - `CERTIFICATE_ARN` (ASF and JPL only) - ARN of the AWS Certificate Manager certificate that you created manually, e.g. `arn:aws:acm:us-west-2:XXXXXXXXXXXX:certificate/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX`
    - `CLOUDFORMATION_ROLE_ARN` (ASF only) - part of the `hyp3-ci` stack that you deployed, e.g. `arn:aws:iam::xxxxxxxxxxxx:role/hyp3-ci-CloudformationDeploymentRole-XXXXXXXXXXXXX`
    - `SECRET_ARN` - ARN for the AWS Secrets Manager Secret that you created manually, e.g. `arn:aws:secretsmanager:us-west-X:XXXXXXXXXXXX:secret:hyp3-foobar-XXXXXX`
    - `V2_AWS_ACCESS_KEY_ID` - AWS access key ID:
      - ASF: for the `github-actions` user (created in step "Enable CI/CD above")
      - JPL: for the service user
      - EDC: created by an ASF developer via Kion
    - `V2_AWS_SECRET_ACCESS_KEY` - The corresponding secret access key
    - `VPC_ID` - ID of the default VPC for this AWS account and region (aws console -> VPC -> Your VPCs, e.g. `vpc-xxxxxxxxxxxxxxxxx`)
    - `SUBNET_IDS` - Comma delimited list (no spaces) of the default subnets for the VPC specified in `VPC_ID` (aws console -> VPC -> Subnets, e.g. `subnet-xxxxxxxxxxxxxxxxx,subnet-xxxxxxxxxxxxxxxxx,subnet-xxxxxxxxxxxxxxxxx,subnet-xxxxxxxxxxxxxxxxx`)

### Create the HyP3 deployment

You will need to add the deployment to the matrix in an existing GitHub Actions `deploy-*.yml` workflow located in the `.github/workflows/` directory, or create
a new one for the deployment. If you need to create a new one, we recommend copying one of the
existing workflows, and then updating all of the fields
as appropriate for your deployment. Also make sure to update the top-level `name` of the workflow and the name
of the branch to deploy from. (This is typically `main` for prod deployments, `develop` for test deployments, or a feature branch name for sandbox deployments.)

> [!TIP]
> If you're deploying from a feature branch, make sure to [protect](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
> it from accidental deletion.

> [!TIP]
> If your CI/CD workflow fails. Delete the "Rolled Back" stack (AWS Manager -> CloudFormation -> Stacks) before re-running the failed job.

The deployment workflow will run as soon as you merge your changes into the branch specified in the workflow file.

### Finishing touches

Once HyP3 is deployed, there are a few follow on tasks you may need to do for a fully functional HyP3 deployment.

#### Create DNS record for new HyP3 API

> [!WARNING]
> This step must be done by an ASF employee.

Open a PR adding a line to https://gitlab.asf.alaska.edu/operations/puppet/-/blob/production/modules/legacy_dns/files/asf.alaska.edu.db
for the new custom domain name (AWS console -> api gateway -> custom domain names -> "API Gateway domain name") of the format
`hyp3-foobar in CNAME <API Gateway domain name>.`. Follow similar examples.

Ask someone from ASF support to review/merge the PR.

Changes should take effect within 15-60 minutes after merging.
Confirm that a Swagger UI is available at your chosen API URL.

Update the [AWS Accounts and HyP3 Deployments](https://docs.google.com/spreadsheets/d/1gHxgVbgQbqFNMQQe042Ku5L2pM6LLTOBDOFgO1FgZeU/) spreadsheet.

> [!TIP]
> While waiting for the DNS PR, you can edit your local DNS name resolution so you can connect to your deployment:
> 1. Retrieve the API Gateway domain name from API Gateway -> Custom Domain Names -> deployment domain name
> 2. Look up the IP address for the API Gateway domain name via `nslookup <gateway-domain-name>`
> 3. Edit your `/etc/hosts` to connect one of the returned IP addresses with your custom domain name, like:
>    ```
>    XX.XX.XXX.XXX   <deployment-name>.asf.alaska.edu
>    ```
> Remember to remove this after the DNS PR is merged!

#### Testing and adding user credits to your hyp3 deployment

After successfully deploying HyP3 and your new DNS record has taken effect (or you've edited your local DNS name resolution), you can test your deployment by accessing the Swagger UI and using the POST `/user` tab to 
check if your user is approved and has credits for running jobs on the deployment. You will need to be authenticated by either providing an Earthdata Login Bearer Token using the "Authorize" button, or by having a valid `asf-urs` cookie, typically logging into [Vertex](https://search.asf.alaska.edu). Interacting with HyP3 should automatically add your user to the DynamoDB table with the default number of credits (typically 0).

To add credits to your (or any) user, log in to the AWS console and navigate to  DynamoDB -> Explore items, then:
1. Find the table with a format like `hyp3-foobar-UsersTable-XXXXXXXXXXXXX`
2. Edit your user record (only present after using the Swagger UI in some way)

You can then return the Swagger UI and use the POST `/jobs` to run a test job and confirm it completes.

#### Optional

<details>
<summary>JPL: Allow a public HyP3 content bucket for JPL accounts</summary>
<br />

By default, JPL commercial AWS accounts have an S3 account level Block All Public
Access set which must be disabled by the JPL Cloud team in order to attach a public
bucket policy to the HyP3 content bucket.

The steps to disable the account level Block All Public Access setting is outlined
in the S3 section here:
https://wiki.jpl.nasa.gov/display/cloudcomputing/AWS+Service+Policies+at+JPL

Once this setting has been disabled, you can attach a public bucket policy to the
HyP3 content bucket by redeploying HyP3 using the `JPL-public` security environment.
</details>

<details>
<summary>All: Grant AWS account permission to pull the hyp3-gamma container</summary>
<br />

*Warning: This step must be done by an ASF employee.*

If your HyP3 deployment uses the `RTC_GAMMA` or `INSAR_GAMMA` job types
and is the first such deployment in this AWS account,
you will need to grant the AWS account permission to pull the `hyp3-gamma` container.

In the **HyP3 AWS account** (not the AWS account for the new deployment),
go to AWS console -> Elastic Container Registry -> hyp3-gamma -> Permissions -> "Edit policy JSON":
1. Add the new AWS account root user to the `Principal` (e.g. `arn:aws:iam::xxxxxxxxxxxx:root`)
2. Update list of account names in the `SID`

</details>

### Deleting a HyP3 deployment

To delete a HyP3 deployment, delete any of the resources created above that are no longer needed.

Before deleting the HyP3 CloudFormation stack,
you should manually empty and delete the `contentbucket` and `logbucket` for the deployment via the S3 console.

## Running the API locally

The API can be run locally for testing and development purposes:

1. Choose an existing HyP3 deployment that you want to connect to.
2. Set up credentials for the corresponding AWS account as described
   [here](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration).
   Also see our [developer docs article](https://github.com/ASFHyP3/.github-private/blob/main/docs/AWS-Access.md#aws-access-keys).
3. If you haven't already, follow the [Developer Setup](#developer-setup) section to clone this repo and activate your conda environment.
4. Edit your local copy of [`tests/cfg.env`](./tests/cfg.env) to specify the names of the DynamoDB tables from the HyP3 deployment.
   Delete all of the `AWS_*` variables.
5. Run the following command, replacing `<profile>` with the AWS config profile that corresponds to the HyP3 deployment:
   ```sh
   AWS_PROFILE=<profile> make run
   ```
6. You should see something like `Running on http://127.0.0.1:8080` in the output.
   Open the URL in your browser and verify that you see the Swagger UI for the locally running API.
7. Click the "Authorize" button in the upper right and input your [Earthdata Login bearer token](https://urs.earthdata.nasa.gov/documentation/for_users/user_token).
8. To verify access, query the `GET /user` endpoint and verify that it returns the correct information for your username.
