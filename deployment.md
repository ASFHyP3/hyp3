# deployment

TODO: move to README

## ASF- and JPL-specific steps

Follow one of the two markdown files provided at [`cicd-stack/`](./cicd-stack/)
for either an ASF deployment or a JPL deployment.

## Create EDL user

Assuming the job spec(s) for your chosen job type(s) require the `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` secrets,
you will need to create an Earthdata Login user for your deployment if you do not already have one:

1. Visit https://urs.earthdata.nasa.gov/home and click "Register"
2. Fill in the required fields
3. Fill in a Study Area
4. After finishing, visit Eulas -> Accept New EULAs and accept "Alaska Satellite Facility Data Access"
5. Log into Vertex as the new user, and confirm you can download files, e.g. https://datapool.asf.alaska.edu/METADATA_SLC/SA/S1A_IW_SLC__1SDV_20230130T184017_20230130T184044_047017_05A3C3_381F.iso.xml
6. Add the new username and password to your team's password manager.

## Create AWS Secrets Manager Secret

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

## Upload SSL cert

Upload the `*.asf.alaska.edu` SSL certificate to AWS ACM.

AWS console -> certificate manager (ACM) -> import certificate

Open https://gitlab.asf.alaska.edu/operations/puppet/-/tree/production/site/modules/certificates/files
- The contents of the `asf.alaska.edu.cer` file go in Certificate body
- The contents of the `asf.alaska.edu.key` file go in Certificate private key
- The contents of the `incommon.cer` file goes in Certificate chain

## Create the GitHub environment

1. Go to https://github.com/ASFHyP3/hyp3/settings/environments -> New Environment
2. Check "required reviewers" and add the appropriate team(s) or user(s)
3. Change "Deployment branches" to "protected branches"
4. Add the following environment secrets:
    - `AWS_REGION` - e.g. `us-west-2`
    - `CLOUDFORMATION_ROLE_ARN` - part of the CI/CD stack that you deployed (above), e.g. `arn:aws:iam::xxxxxxxxxxxx:role/hyp3-ci-CloudformationDeploymentRole-XXXXXXXXXXXXX`
    - `SECRET_ARN` - ARN for the AWS Secrets Manager Secret that you created manually (above)
    - `V2_AWS_ACCESS_KEY_ID` - Access key ID that you created for the `github-actions` user (above)
    - `V2_AWS_SECRET_ACCESS_KEY` - Secret access key that you created for the `github-actions` user (above)
    - `VPC_ID` - ID of the default VPC for this AWS account and region (aws console -> vpc -> your VPCs, e.g. `vpc-xxxxxxxxxxxxxxxxx`)
    - `SUBNET_IDS` - Comma delimited list (no spaces) of the default subnets for this VPC (aws console -> vpc -> subnets, e.g. `subnet-xxxxxxxxxxxxxxxxx,subnet-xxxxxxxxxxxxxxxxx,subnet-xxxxxxxxxxxxxxxxx,subnet-xxxxxxxxxxxxxxxxx`)
    - `CERTIFICATE_ARN` - ARN of the AWS Certificate Manager certificate that you imported manually, above (aws console -> certificate manager -> list certificates, e.g. `arn:aws:acm:us-west-2:xxxxxxxxxxxx:certificate/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

## Create the HyP3 deployment

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

## Grant AWS account permission to pull the hyp3-gamma container

If your HyP3 deployment uses the `RTC_GAMMA` or `INSAR_GAMMA` job types
and is the first such deployment in this AWS account,
you will need to grant the AWS account permission to pull the `hyp3-gamma` container.

In the **HyP3 AWS account** (not the AWS account for the new deployment),
go to AWS console -> elastic container registry -> hyp3-gamma -> permissions -> "edit policy json":
1. Add the new AWS account root user to the `Principal` (e.g. `arn:aws:iam::xxxxxxxxxxxx:root`)
2. Update list of account names in the `SID`

## Create DNS record for new HyP3 API

Open a PR adding a line to https://gitlab.asf.alaska.edu/operations/puppet/-/blob/production/modules/legacy_dns/files/asf.alaska.edu.db
for the new custom domain name (AWS console -> api gateway -> custom domain names -> "API Gateway domain name").

Ask the Platform team in the `~development-support` channel in Mattermost to review/merge the PR.

Changes should take effect within 15-60 minutes after merging.
Confirm that a Swagger UI is available at your chosen API URL.

Update the [AWS Accounts and HyP3 Deployments](https://docs.google.com/spreadsheets/d/1gHxgVbgQbqFNMQQe042Ku5L2pM6LLTOBDOFgO1FgZeU/) spreadsheet.
