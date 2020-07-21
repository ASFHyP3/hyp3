# HyP3
![Static code analysis](https://github.com/ASFHyP3/hyp3/workflows/Static%20code%20analysis/badge.svg)
![Deploy to AWS](https://github.com/ASFHyP3/hyp3/workflows/Deploy%20to%20AWS/badge.svg)
![Run tests](https://github.com/ASFHyP3/hyp3/workflows/Run%20tests/badge.svg)

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

- IAM role configured for API gateway access logging
- IAM user and roles for automated CloudFormation deployments
- HyP3 plugin container images and tags:
  - RTC-GAMMA
- S3 bucket for CloudFormation deployment artifacts
- DNS record for custom API domain name
- SSL certificate in AWS Certificate Manager for custom API domain name
- EarthData Login account authorized to download data from ASF
- default VPC

### Stack Parameters
Review the parameters in [cloudformation.yml](cloudformation.yml) for deploy time configuration options.

### Deploy with CloudFormation

- Install API dependencies
```sh
pip install -r api/requirements.txt -t api/src
```

- Package the CloudFormation template
```sh
aws cloudformation package \
            --template-file cloudformation.yml \
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
                "EDLUsername=<EDL Username to download products>" \
                "EDLPassword=<EDL Password to download products>" \
                "RtcGammaImage=<location of RtcGammaImage to use>" \
                "DomainName=<Domain Name>" \
                "CertificateArn=<arn for ssl certificate>"
```
- Check API at `<Domain Name>/ui`


## Testing the API
The HyP3 API source contains test files in `/API/tests/`. To run them you need to do a bit of setup first.

- Add hyp3-api to python path
```sh
export PYTHONPATH="${PYTHONPATH}:`pwd`/api/src"
```
- Setup environment variables
```sh
export $(cat /api/test/cfg.env | xargs)
```
- Run tests
```sh
pytest api/src/
```

## Running the API Locally
The API can be run locally to verify changes, but must be tied to existing orchestration.

- Setup aws credentials in your environment [Documentation by AWS](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration)
- setup environment variables
  - `TABLE_NAME=<jobs table id>`
  - `MONTHLY_JOB_QUOTA_PER_USER=100`
  - `AUTH_PUBLIC_KEY=123456789` *we use this auth config so that we can set the cookie ourselves to a known good value*
  - `AUTH_ALGORITHM=HS256`
- Add hyp3-api to python path
```sh
export PYTHONPATH="${PYTHONPATH}:`pwd`/api/src"
```
- run API
```sh
python3 api/src/hyp3_api/__main__.py
```
- In order to connect you will need to include the following cookie
```
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1cnMtdXNlci1pZCI6InVzZXIiLCJleHAiOjIxNTk1MzY1MzIzLCJ1cnMtZ3JvdXBzIjpbeyJuYW1lIjoiYXV0aC1ncm91cCIsImFwcF91aWQiOiJhdXRoLXVpZCJ9XX0.Xa0T6kRD5nihlH6UneYUpt1pzumjYre0fWVrxOq-1pw
```
