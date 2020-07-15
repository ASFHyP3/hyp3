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