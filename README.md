# hyp3
![Static code analysis](https://github.com/ASFHyP3/hyp3/workflows/Static%20code%20analysis/badge.svg)
![Deploy to AWS](https://github.com/ASFHyP3/hyp3/workflows/Deploy%20to%20AWS/badge.svg)
![Run tests](https://github.com/ASFHyP3/hyp3/workflows/Run%20tests/badge.svg)

A processing environment for running RTC Gamma container jobs in Amazon Web Services.

## Table of contents
- [Deployment](#deployment)
  - [Prerequisites](#prerequisites)
  - [Stack Parameters](#stack-parameters)
  - [Deploy with Cloudformation](#deploy-with-cloudformation)
- [Testing](#testing)
- [Running the API Locally](#running-the-api-locally)
## Deployment


### Prerequisites
These resources are required for a successful deployment, but managed separately:

- IAM role configured for api gateway access logging
- IAM user and roles for automated cloudformation deployments
- RTC Gamma container image repository and tag
- S3 bucket for cloudformation deployment artifacts
- DNS record for custom api domain name
- SSL certificate in AWS Certificate Manager for custom api domain name
- Earthdata Login account authorized to download data from ASF
- default VPC

### Stack Parameters
Review Parameters in cloudformation.yml for deploy time configuration options.

### Deploy with Cloudformation

- Install and package dependancies for api
```sh
pip install -r api/requirements.txt -t api/src
aws cloudformation package \
            --template-file cloudformation.yml \
            --s3-bucket <Cloud Formation artifact bucket> \
            --output-template-file packaged.yml
```

- deploy to AWS with Cloud Formation
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

## Testing
The HyP3 api source contains test files in `/api/tests/`. To run them you need to do a bit of setup first.

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
  - TABLE_NAME=\<jobs table id\>
  - MONTHLY_JOB_QUOTA_PER_USER=100
  - AUTH_PUBLIC_KEY=123456789 `we use this auth config so that we can set the cookie ourselves to a known good value`
  - AUTH_ALGORITHM=HS256
- Add hyp3-api to python path
```sh
export PYTHONPATH="${PYTHONPATH}:`pwd`/api/src"
```
- run api
```sh
python3 api/src/hyp3_api/__main__.py
```
- In order to connect you will need to include the following cookie
```eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1cnMtdXNlci1pZCI6InVzZXIiLCJleHAiOjE1OTUxMDEzMjcsInVycy1ncm91cHMiOlt7Im5hbWUiOiJhdXRoLWdyb3VwIiwiYXBwX3VpZCI6ImF1dGgtdWlkIn1dfQ.x8CMKRwQn8LgtWFhz8m68mTGfW9bfsbBh-eiPPDFUpE```

