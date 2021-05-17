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

### Prerequisites
These resources are required for a successful deployment, but managed separately:

- HyP3 plugin container images and tags:
  - RTC_GAMMA
  - INSAR_GAMMA
  - AUTORIFT
- S3 bucket for CloudFormation deployment artifacts
- DNS record for custom API domain name
- SSL certificate in AWS Certificate Manager for custom API domain name
- EarthData Login account authorized to download data from ASF
- default VPC
- IAM user and roles for automated CloudFormation deployments (if desired)

### Stack Parameters
Review the parameters in [cloudformation.yml](apps/main-cf.yml) for deploy time configuration options.

### Deploy with CloudFormation

- Install dependencies for build and run
```sh
pip install -r requirements-all.txt
```

- Render cloudformation templates
```sh
cd apps
python render_cf.py --job-types-file ../job_types.yml
cd ..
```

- Install API dependencies (requires pip for python 3.8)

```sh
pip install -r apps/api/requirements-api.txt -t apps/api/src
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
                "ImageTag=<docker image tag>" \
                "DomainName=<Domain Name>" \
                "CertificateArn=<arn for ssl certificate>" \
                "MonthlyJobQuotaPerUser=<quota>"
```
- Check API at `https://<Domain Name>/ui`


## Testing the API
The HyP3 API source contains test files in `tests/api/`. To run them you need to do a bit of setup first.

- Add hyp3-api and tests to python path
```sh
export PYTHONPATH="${PYTHONPATH}:`pwd`/apps/api/src:`pwd`/tests"
```
- Setup environment variables
```sh
export $(cat tests/api/cfg.env | xargs)
```
- Install test requirements
```sh
pip install -r apps/api/requirements-all.txt
```

- Render cloudformation templates
```sh
cd apps
python render_cf.py --job-types-file ../job_types.yml
cd ..
```

- Run tests
```sh
pytest tests/api/
```

## Running the API Locally
The API can be run locally to verify changes, but must be connected to an existing DynamoDB jobs table.

- Setup aws credentials in your environment [Documentation by AWS](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration)
- Setup environment variables
  - `TABLE_NAME=<jobs table id>`
  - `MONTHLY_JOB_QUOTA_PER_USER=25`
  - `AUTH_PUBLIC_KEY=123456789` *we use this auth config so that we can set the cookie ourselves to a known good value*
  - `AUTH_ALGORITHM=HS256`
  - `SYSTEM_AVAILABLE=true`
- Add hyp3-api to python path
```sh
export PYTHONPATH="${PYTHONPATH}:`pwd`/apps/api/src"
```
- run API
```sh
python3 apps/api/src/hyp3_api/__main__.py
```
- In order to use you will need to include the following cookie
```
asf-urs=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1cnMtdXNlci1pZCI6InVzZXIiLCJleHAiOjIxNTk1Mzc0OTYyLCJ1cnMtZ3JvdXBzIjpbeyJuYW1lIjoiYXV0aC1ncm91cCIsImFwcF91aWQiOiJhdXRoLXVpZCJ9XX0.hMtgDTqS5wxDPCzK9MlXB-3j6MAcGYeSZjGf4SYvq9Y
```
