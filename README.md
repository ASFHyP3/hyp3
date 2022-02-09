# HyP3
![Static code analysis](https://github.com/ASFHyP3/hyp3/workflows/Static%20code%20analysis/badge.svg)
![Deploy to AWS](https://github.com/ASFHyP3/hyp3/workflows/Deploy%20to%20AWS/badge.svg)
![Run tests](https://github.com/ASFHyP3/hyp3/workflows/Run%20tests/badge.svg)

[![DOI](https://zenodo.org/badge/259996151.svg)](https://zenodo.org/badge/latestdoi/259996151)


A processing environment for HyP3 Plugins in AWS.

## Table of contents
- [Deployment](#deployment)
  - [Prerequisites](#prerequisites)
  - [Stack Parameters](#stack-parameters)
  - [Deploy with CloudFormation](#deploy-with-cloudformation)
- [Testing the API](#testing-the-api)
- [Running the API Locally](#running-the-api-locally)

## Deployment

The deployment steps below describe how to deploy to a general AWS account you own/administer.
HyP3 does support deploying to more secure environments which may require additional steps and are
described in [`docs/deployments`](docs/deployments).

### Prerequisites
These resources are required for a successful deployment, but managed separately:

- HyP3 plugin container images and tags. Current plugins are defined in [`job_spec`](./job_spec).
- S3 bucket for CloudFormation deployment artifacts
- DNS record for custom API domain name
- SSL certificate in AWS Certificate Manager for custom API domain name
- EarthData Login account authorized to download data from ASF
- default VPC
- IAM user and roles for automated CloudFormation deployments (if desired)

### Stack Parameters
Review the parameters in [cloudformation.yml](apps/main-cf.yml) for deploy time configuration options.

### Deploy with CloudFormation

To deploy HyP3 with reasonable defaults, follow the steps below. For more advanced
deployment configuration, see the [deployment GitHub Action](.github/actions/deploy-hyp3/action.yml).

From the repository root, 

- Install dependencies for build and run
```sh
make install
```

- Install Python dependencies for AWS Lambda functions (requires pip for python 3.8)
```sh
make build
```

- Package the CloudFormation template
```sh
aws cloudformation package \
            --template-file apps/main-cf.yml \
            --s3-bucket <CloudFormation artifact bucket> \
            --output-template-file packaged.yml
```

- Deploy to AWS with CloudFormation
```sh
aws cloudformation deploy \
            --stack-name <name of your HyP3 Stack> \
            --template-file packaged.yml \
            --role-arn <arn for your deployment user/role> \
            --capabilities CAPABILITY_IAM \
            --parameter-overrides \
                "VpcId=<default vpc>" \
                "SubnetIds=<comma separated list of subnet ids>" \
                "EDLUsername=<EDL Username to download products>" \
                "EDLPassword=<EDL Password to download products>" \
                "DomainName=<Domain Name>" \
                "CertificateArn=<arn for ssl certificate>"
```
- Check API at `https://<Domain Name>/ui`

- (Optional) clean render and build artifacts
```sh
make clean
```
*Note: this will remove any [untracked files](https://git-scm.com/docs/git-ls-files#Documentation/git-ls-files.txt--o)
in the `apps/` or `lib/dynamo/` directory.*

## Running the Tests
Tests for each HyP3 module are located in `tests/`. To run them you need to do a bit of setup first.

- Install test requirements (this must be done from the root of the repo for libraries to resolve correctly)
```sh
make install
```

- run the tests
```sh
make tests
```

## Running the API Locally
The API can be run locally to verify changes, but must be connected to an existing DynamoDB jobs table.

- Setup aws credentials in your environment [Documentation by AWS](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration)
- Setup environment variables in `test/cfg.env` to desired values (you must change the names of any DynamoDB table to one that exists)

- run API
```sh
make run
```
- In order to use you will need to include the following cookie
```
asf-urs=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1cnMtdXNlci1pZCI6InVzZXIiLCJleHAiOjIxNTk1Mzc0OTYyLCJ1cnMtZ3JvdXBzIjpbeyJuYW1lIjoiYXV0aC1ncm91cCIsImFwcF91aWQiOiJhdXRoLXVpZCJ9XX0.hMtgDTqS5wxDPCzK9MlXB-3j6MAcGYeSZjGf4SYvq9Y
```
