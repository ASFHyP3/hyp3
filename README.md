# hyp3
![Static code analysis](https://github.com/ASFHyP3/hyp3/workflows/Static%20code%20analysis/badge.svg)
![Deploy to AWS](https://github.com/ASFHyP3/hyp3/workflows/Deploy%20to%20AWS/badge.svg)

A processing environment for running RTC Gamma container jobs in Amazon Web Services.

# Components

# Deployment

## Prerequisites

These resources are required for a successful deployment, but managed separately:

- IAM role configured for api gateway access logging
- IAM user and roles for automated cloudformation deployments
- RTC Gamma container image repository and tag
- S3 bucket for cloudformation deployment artifacts
- DNS record for custom api domain name
- SSL certificate in AWS Certificate Manager for custom api domain name
- Earthdata Login account authorized to download data from ASF
- default VPC

## Stack Parameters
