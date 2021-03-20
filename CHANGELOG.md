# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0]
### Added
- `GET /jobs` now pages results, large queries (that require paging) will contain a `next`
  key in the root level of the json response with a URL to fetch subsequent pages
- `GET /jobs` now accepts a `job_type` query parameter

## [0.8.17]
### Added
- Exposed new `include_rgb` api parameter for RTC_GAMMA jobs

## [0.8.16]
### Changed
- `get_files.py` now only includes product files ending in `.zip` or `.nc` in the `files` list returned
  in `GET /jobs` API responses

## [0.8.15]
### Changed
- S3 content bucket now allows public `s3:ListBucket` and `s3:GetObjectTagging`

## [0.8.14]
### Added
- Jobs now include a `logs` key containing a list of log file download urls

## [0.8.13]
### Changed
- Increased max capacity for compute environment to 1600 vCPUs

## [0.8.12]
### Changed
- Improved response latency when submitting new jobs via `POST /jobs`

## [0.8.11]
### Added
- `GET /jobs` responses now include `s3.bucket` and `s3.key` entries for each file to facilitate interacting with
  products using s3-aware tools.

### Fixed
- AUTORIFT jobs now correctly accept Sentinel-2 granules using Earth Search IDs of 23 characters.

## [0.8.10]
### Added
- AutoRIFT jobs now allow submission with Landsat 8 Collection 2 granules

### Changed
- AutoRIFT jobs now only accept Sentinel-2 L1C granules, rather than any Sentinel-2 granules

### Removed
- API responses are no longer validated against the OpenAPI schema.  `GET /jobs` requests for jobs
  with legacy parameter values (e.g. S2 L2A granules) will no longer return HTTP 500 errors.

## [0.8.9]
### Changed
- INSAR_GAMMA jobs now use the [hyp3-gamma](https://github.com/ASFHyP3/hyp3-gamma) plugin to do processing

## [0.8.8]
### Changed
- RTC_GAMMA jobs now use the [hyp3-gamma](https://github.com/ASFHyP3/hyp3-gamma) plugin to do processing

## [0.8.7]
### Added
- Autorift jobs now allow submission with Sentinel 2 granules

## [0.8.6]
### Added
- A new `include_scattering_area` paramter has been added for `RTC_GAMMA` jobs, which includes a GeoTIFF of scattering area in the product package. This supports creation of composites of RTC images using Local Resolution Weighting per Small (2012) https://doi.org/10.1109/IGARSS.2012.6350465.
- Cloudwatch request metrics are now enabled for the S3 content bucket

## [0.8.5]
### Changed
- Api Gateway access logs are now in JSON format for easier parsing by Cloudwatch Insights
- Api Gateway access logs now include `responseLatency` and `userAgent` fields.  Unused `caller` and `userId` fields are no longer included.

## [0.8.4]
### Changed
- `/` now redirects to `/ui`

## [0.8.3]
### Changed
- Increased compute to allow 200 concurrent instances.

## [0.8.2]
### Changed
- Refactored dynamodb interactions
  - `dynamo.py` in the api code now manages all dynamodb interactions for the api
  - added tests for new dynamo module
  - added paging for dynamodb query calls

## [0.8.1]
### Added
- Added Code of Conduct and Contributing Guidelines

### Changed
- `MonthlyJobQuotaPerUser` stack parameter no longer has a default, and the value can now be set to zero.
  - Value is now set to `200` for ASF deployments.
  - Value is now set to `0` for the autoRIFT deployment.
- `POST /jobs` requests now allow up to 200 jobs per request, up from 25

## [0.8.0]
### Added
- User table which can be used to add custom quotas for users, users not in the table will still have the default.
- GET /jobs/{job_id} API endpoint to search for a job by its job_id

## [0.7.5]
### Added
- Api and processing errors will now post to a SNS topic

### Changed
* Parameters for `INSAR_GAMMA` jobs have been updated to reflect hyp3-insar-gamma [v2.2.0](https://github.com/ASFHyP3/hyp3-insar-gamma/blob/develop/CHANGELOG.md#220).

## [0.7.4]
### Changed
- API behavior for different job types is now defined exclusively in `job_types.yml`.  Available parameter types must still be defined in `apps/api/src/hyp3_api/api-sec/job_parameters.yml.j2`, and available validation rules must still be defined in `apps/api/src/hyp3_api/validation.py`.

## [0.7.3]
### Changed
- Added `AmazonS3ReadOnlyAccess` permission to batch task role to support container jobs fetching input data from S3.

## [0.7.2]
### Fixed
- RTC_GAMMA jobs now use the user-provided value for the speckle filter parameter.  Previously, the user-provided value was ignored and all jobs processed using the default value (false).

## [0.7.1]
### Changed
- Hyp3 now uses jinja templates in defining CloudFormation templates and the StepFunction definition, rendered at buildtime.
- Job types are now defined only in the API spec and the `job_types.yml` file, no job specific information needs to be added to AWS resource definitions.
- Static Analysis now requires rendering before run.

## [0.7.0]
### Added
- Added a new `AUTORIFT` job type for processing a pair of Sentinel-1 SLC IW scenes using [autoRIFT](https://github.com/leiyangleon/autoRIFT). For details, refer to the [hyp3-autorift](https://github.com/ASFHyP3/hyp3-autorift) plugin repository.

### Changed
- Updated readme deployment instructions.
- Clarified job parameter descriptions in OpenAPI specification.
- Moved step function definition into it's own file and added static analysis on step funciton definition.
- Split OpenAPI spec into multiple files using File References to resolve, static analysis change from openapi-spec-validator to prance.

## [0.6.1]
### Added
- `GET /user` response now includes a `job_names` list including all distinct job names previously submitted for the current user

### Changed
- API is now deployed using Api Gateway V2 resources, resulting in lower response latency.

## [0.6.0]
### Added
- Added a new `INSAR_GAMMA` job type for producing an interferogram from a pair of Sentinel-1 SLC IW scenes using [GAMMA](https://www.gamma-rs.ch/software).  For details, refer to the [hyp3-insar-gamma](https://github.com/ASFHyP3/hyp3-insar-gamma) plugin repository.

### Changed
- All job types requiring one or more granules now expose a single `granules` job parameter, formatted as a list of granule names:
  - `"granules": ["myGranule"]` for `RTC_GAMMA` jobs
  - `"granules": ["granule1", "granule2"]` for `INSAR_GAMMA` jobs

  Note this is a breaking change for `RTC_GAMMA` jobs.
- Browse and thumbnail URLs for `RTC_GAMMA` jobs will now be sorted with the amplitude image first, followed by the rgb image, in `GET /jobs` responses.

## [0.5.1]
### Fixed
- Resolved HTTP 500 error when submitting jobs with a resolution with decimal precision (e.g. `30.0`)

## [0.5.0]
### Changed
- The `dem_matching`, `speckle_filter`, `include_dem`, and `include_inc_map` api parameters are now booleans instead of strings.
- The `resolution` api parameter is now a number instead of a string, and the `10.0` option has been removed.

## [0.4.0]
### Changed
- Implemented 0.15° buffer and 20% threshold in DEM coverage checks when submitting new jobs.  As a result slightly more granules will be rejected as having insufficient coverage.

### Removed
- Removed optional `description` field for jobs

## [0.3.9]
### Added
- Unit tests for `get-files` lambda function

### Fixed
- Resolved HTTP 500 errors for `POST /jobs` requests when the optional `validate_only` parameter was not provided
- Jobs encountering unexpected errors in the `get-files` step will now correctly transition to a `FAILED` status

## [0.3.8]
### Added
- `POST /jobs` now accepts a `validate_only` key at root level, set to true to skip submitting jobs but run api validation.

## [0.3.7]
### Fixed
- `get-files` get expiration only from product

## [0.3.6]
### Fixed
- `get-files` step functions AMI roles for tags


## [0.3.5]
### Added
- `POST /jobs` now accepts custom job parameters when submitting jobs
- `GET /jobs` now shows parameters job was run with

### Changed
- `get_files.py` now uses tags to identify file_type instead of path

## [0.3.4]
### Added
- Name field to job parameter, set in the same way as description but with max length of 20

## [0.3.3]
### Added
- Administrators can now shut down Hyp3-api by setting SystemAvailable flag to false in CloudFormation Template and deploying

## [0.3.2]
### Added
- Retry policies to improve reliability

### Changed
- POST /jobs now accepts GRDH Files in the IW beam mode.
- Removed scaling rules and moved to MANAGED compute environment to run jobs

## [0.3.1]
### Added
- POST /jobs now checks granule intersects DEM Coverage map to provide faster feedback on common error cases
### Fixed
- Resolved bug not finding granules when submitting 10 unique granules in a RTC_GAMMA job

## [0.3.0] - 2020-07-22
### Added
- README.md with instructions for deploying, testing, and running the application
- Descriptions for all parameters in the top level cloudformation template
- Descriptions for all schema objects in the OpenAPI specification
### Changed
- Reduced monthly job quota per user from 100 to 25
- Reduced maximum number of jobs allowed in a single POST /jobs request from 100 to 25
### Removed
- Removed user authorization requirement for submitting jobs
- Removed is_authorized field from GET /user response

## [0.2.0] - 2020-07-14
### Added
- New GET /user API endpoint to query job quota and jobs remaining
- browse image key for each job containing a list of urls for browse images
- browse images expire at the same time as products
- thumbnail image key for each job containing a list of urls for thumbnail images
- thubnail images expire at the same time as products

## [0.1.0] - 2020-06-08
### Added
- API checks granule exists in CMR and rejects jobs with granules that are not found
