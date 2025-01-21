# HyP3
![Static code analysis](https://github.com/ASFHyP3/hyp3/workflows/Static%20code%20analysis/badge.svg)
![Deploy to AWS](https://github.com/ASFHyP3/hyp3/workflows/Deploy%20to%20AWS/badge.svg)
![Run tests](https://github.com/ASFHyP3/hyp3/workflows/Run%20tests/badge.svg)

[![DOI](https://zenodo.org/badge/259996151.svg)](https://zenodo.org/badge/latestdoi/259996151)


A processing environment for HyP3 Plugins in AWS.

## Table of contents
- [HyP3](#hyp3)
  - [Table of contents](#table-of-contents)
  - [Developer Setup](#developer-setup)
  - [Deployment](#deployment)
    - [Prerequisites](#prerequisites)
    - [Stack Parameters](#stack-parameters)
    - [Deploy with CloudFormation](#deploy-with-cloudformation)
  - [Running the API Locally](#running-the-api-locally)

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
3. Run the tests
   ```
   make tests
   ```

## Deployment

The deployment steps below describe how to deploy to a general AWS account you own/administer.
HyP3 does support deploying to more secure environments which may require additional steps and are
described in [`docs/deployments`](docs/deployments).

### Prerequisites
These resources are required for a successful deployment, but managed separately:

- HyP3 plugin container images and tags. Current plugins are defined in [`job_spec`](./job_spec).
- S3 bucket for CloudFormation deployment artifacts
- EarthData Login account authorized to download data from ASF
- IAM role configured for [REST API access logging](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-logging.html#set-up-access-logging-permissions)
- default VPC
- IAM user and roles for automated CloudFormation deployments (if desired)
- AWS Secrets Manager Secret containing key-value pairs for all secrets listed in the deployed [`job_spec`s](./job_spec)
- For Earthdata Cloud deployments:
  - SSL certificate in AWS Certificate Manager for custom CloudFront domain name
  - ID of the CloudFront Origin Access Identity used to access data in S3 
- For non-Earthdata Cloud deployments:
  - DNS record for custom API domain name
  - SSL certificate in AWS Certificate Manager for custom API domain name

### Stack Parameters
Review the parameters in [cloudformation.yml](apps/main-cf.yml) for deploy time configuration options.

### Deploy with CloudFormation

From the repository root,

1. Define the CloudFormation and build parameters for the HyP3 deployment
     1. Create a copy of `hyp3.example`, and rename it `hyp3.env`
     1. Update its environment variable values (at least those in the "required" section)

1. (Optional) Create a deployment image that matches the AWS Lambda Python3.13 runtime environment
   
   *Note: Requires a running Docker Engine*
   ```sh
   make image
   ```

1. (Optional) If you created a HyP3 deployment image with `make image`, run a shell on it
   ```sh 
   make shell
   ```

1. Install dependencies for build and run
   ```sh
   make install
   ```

1. Install Python dependencies for AWS Lambda functions (requires pip for python 3.13)
   ```sh
   make build
   ```

1. Package the CloudFormation template
   ```sh
   make package
   ```

1. Deploy HyP3 With CloudFormation
   ```sh
   make deploy
   ```

1. Check API at `https://<Domain Name>/ui`

1. (Optional) clean render and build artifacts
   
   *Notes:* 
      - *Run this outside of your HyP3 deployment container, as it requires git and removes the image*
      - *This will remove any [untracked files](https://git-scm.com/docs/git-ls-files#Documentation/git-ls-files.txt--o) in the `apps/` or `lib/dynamo/` directory.*  

      ```sh
      make clean
      ```

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
