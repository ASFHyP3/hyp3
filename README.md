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
The following Parameters can be provided at deploy-time to change or configure the stack:
- VpcId: 

- EDLUsername: Earth Data Login username to use when downloading products

- EDLPassword: Eatch Data Login password to use when downloading products

- RtcGammaImage: link to Rtc-Gamma processing image to use when running RTC-GAMMA jobs

- ProductLifetimeInDays: Number of days to keep files before deleating them

- AuthPublicKey: Public key for jwt auth provider, if using https://auth.asf.alaska.edu then keep default.
    Default: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDBU3T16Db/88XQ2MTHgm9uFALjSJAMSejmVL+tO0ILzHw2OosKlVb38urmIGQ+xMPXTs1AQQYpJ/CdO7TaJ51pv4iz+zF0DYeUhPczsBEQYisLMZUwedPm9QLoKu8dkt4EzMiatQimBmzDvxxRkAIDehYh468phR6zPqIDizbgAjD4qgTd+oSA9mDPBZ/oG1sVc7TcoP93FbO9u1frzhjf0LS1H7YReVP4XsUTpCN0FsxDAMfLpOYZylChkFQeay7n9CIK8em4W4JL/T0PC218jXpF7W2p92rfAQztiWlFJc66tt45SXAVtD1rMEdWGlzze4acjMn4P7mugHHb17igtlF82H/wpdm84qTPShvBp/F4YZejgAzOAxzKVbCQ8lrApk1XYVDRAVk3AphfvNK5IC/X9zDSXstH9U94z8BTjkL2fR4eKzFu5kkvVoGHAACIv72QvH06Vwd0PNzLyaNXr9D5jO61EbR4RfpbzvAG0IzgXsUq0Rj7qwvzTCu6yLwTi/fn9bmRaOQNPtBch4ai5w7cfUWe2r7ZPv31AXPm1A+aGXvYTEZkiQMrBN/dXlNdUmafNNDoMBm/frQhMl+2DZp+C9GXCr2Z/JmYUHO8PaEj6UyYTkkrmtZNlZ43Nd2TblPEzL0pprJM9MxEf2Peaai8GKmTJz6C5tSGU+XdZQ== root@9dce6b43747e

- AuthAlgorithm: algorithm for jwt auth provider, if using https://auth.asf.alaska.edu then keep default.
    Default: RS256

- AuthGroupName: Name of EDL group for restriction of user submission of jobs
 
- AuthAppUid: Name of jwt auth provider app uid, if using https://auth.asf.alska.edu then keep default
    Default: asf_urs

- DomainName: dns domain record that will be used to invoke this api

  CertificateArn: ARN of Certificate setup previously for this domain name

  MonthlyJobQuotaPerUser: number of jobs a single user is allowed each month.
    Default: 100

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
                "CertificateArn=<arn for ssl certificate>" \
                "AuthGroupName=<EDL group name for access control>"
```

## Testing
The HyP3 api source contains test files in `/api/tests/`. To run them you need to do a bit of setup first.

- Add hyp3-api to python path
```sh
export PYTHONPATH="${PYTHONPATH}:`pwd`/api/src"
```
- Setup environment variables
```sh
export (cat /api/test/cfg.env | xargs)
```
- Run tests
```sh
pytest /api/src/
```

## Running the API Locally
The API can be run locally to verify changes, but must be tied to existing orchestration.

- Setup aws credentials in your environment [Documentation by AWS](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration)
- setup environment variables
  - TABLE_NAME=<jobs table id>
  - MONTHLY_JOB_QUOTA_PER_USER=100
  - AUTH_PUBLIC_KEY=123456789 `we use this auth config so that we can set the cookie ourselves to a known good value`
  - AUTH_ALGORITHM=HS256
  - AUTH_GROUP_NAME=auth-group
  - AUTH_APP_UID=auth-uid
- Add hyp3-api to python path
```sh
export PYTHONPATH="${PYTHONPATH}:`pwd`/api/src"
```
- run api
```sh
python3 /api/src/hyp3_api/__main__.py
```

in order to connect you will need to include the following cookie
```eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1cnMtdXNlci1pZCI6InVzZXIiLCJleHAiOjE1OTUxMDEzMjcsInVycy1ncm91cHMiOlt7Im5hbWUiOiJhdXRoLWdyb3VwIiwiYXBwX3VpZCI6ImF1dGgtdWlkIn1dfQ.x8CMKRwQn8LgtWFhz8m68mTGfW9bfsbBh-eiPPDFUpE```

