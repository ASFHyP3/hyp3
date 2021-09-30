# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.0](https://github.com/ASFHyP3/hyp3/compare/v2.4.3...v2.5.0)
### Added
- Exposed new `include_displacement_maps` API parameter for INSAR_GAMMA jobs, which will cause both a line-of-sight
  displacement and a vertical displacement GEOTIFF to be included in the product.

### Deprecated
- The `include_los_displacement` API parameter for INSAR_GAMMA jobs has been deprecated in favor of the
  `include_displacement_maps` parameter, and will be removed in the future.

## [2.4.3](https://github.com/ASFHyP3/hyp3/compare/v2.4.2...v2.4.3)
### Changed
- The `logs` attribute in `GET /jobs` responses is now only populated for FAILED jobs, and will be an empty list for SUCCEEDED jobs

## [2.4.2](https://github.com/ASFHyP3/hyp3/compare/v2.4.1...v2.4.2)
### Added
- `POST /subscriptions` requests may now include a `validate_only` key which when set to `true` will not add the subscription
to the database but still validate it.
- in `POST /subscriptions` requests, `search_parameters` and `job_specification` are now included under `subscription`
- `GET /subscriptions` requests now include query parameters
  - `name` gets only subscriptions with the given name
  - `job_type` gets only subscriptions with the given job type
  - `enabled` gets only subscriptions where `enabled` matches
- subscriptions now include `creation_date` which indicates date and time of subscription creation, responses from 
`GET /subscriptions` are sorted by `creation_date` decending


## [2.4.1](https://github.com/ASFHyP3/hyp3/compare/v2.4.0...v2.4.1)
### Added
- `PATCH /subscriptions` requests may now update a subscription's `enabled` attribute in addition to `end_date`

## [2.4.0](https://github.com/ASFHyP3/hyp3/compare/v2.3.0...v2.4.0)
### Added
- `GET /jobs` responses now include a `subscription_id` field for jobs created by subscriptions
- `GET /jobs` requests now may include a `subscription_id` query parameter to limit jobs based on subscription_id
- Subscriptions are now evaluated every 16 minutes, instead of every hour

## [2.3.0](https://github.com/ASFHyP3/hyp3/compare/v2.2.0...v2.3.0)
### Added
- `/subscriptions` endpoint which allows a user to define a subscription with search and processing criteria
  - `POST /subscriptions` to create a subscription
  - `GET /subscriptions` to list all subscriptions for the user
  - `PATCH /subscriptions/<subscription_id>` to update the end date of a subscription
  - `GET /subscriptions/<subscription_id>` to list the information for a specific subscription
- `process_new_granules` app which searches for unprocessed granules related to subscriptions and automatically starts
  jobs for them as they become available.

## [2.2.0](https://github.com/ASFHyP3/hyp3/compare/v2.1.1...v2.2.0)
### Added
- HyP3 content bucket now allows Cross Origin Resource Headers
- Exposed new `apply_water_mask` API parameter for INSAR_GAMMA jobs, which sets pixels
  over coastal and large inland waterbodies as invalid for phase unwrapping.

## [2.1.1](https://github.com/ASFHyP3/hyp3/compare/v2.1.0...v2.1.1)
### Changed
- Modified retry strategies for Batch jobs and UploadLog lambda to address scaling errors

## [2.1.0](https://github.com/ASFHyP3/hyp3/compare/v2.0.4...v2.1.0)
### Added
- `lib/dynamo` library to allow sharing common code among different apps.

## Changed
- `POST /jobs` responses no longer include the `job_id`, `request_time`, `status_code`, or `user_id` fields when `validate_only=true` 
- moved dynamodb functionality from `hyp3_api/dynamo` to `lib/dynamo`
- moved job creation buisness logic from `hyp3_api/handlers` to `lib/dynamo`

## [2.0.4](https://github.com/ASFHyP3/hyp3/compare/v2.0.3...v2.0.4)
### Added
- `AutoriftNamingScheme` CloudFormation parameter to set the naming scheme for autoRIFT products

## [2.0.3](https://github.com/ASFHyP3/hyp3/compare/v2.0.2...v2.0.3)
### Changed
- Sentinel-2 autoRIFT jobs now reserve 3/4 less memory, allowing more jobs to be run in parallel

## [2.0.2](https://github.com/ASFHyP3/hyp3/compare/v2.0.1...v2.0.2)
### Changed
- Increased default job quota to 1,000 jobs per user per month

## [2.0.1](https://github.com/ASFHyP3/hyp3/compare/v2.0.0...v2.0.1)
### Changed
- Allow the UI to be accessed from `/ui/` as well as `/ui`
- POST `/jobs` now generates an error for Sentinel-1 granules with partial-dual polarizations,
  fixes [#376](https://github.com/ASFHyP3/hyp3/issues/376)

## [2.0.0](https://github.com/ASFHyP3/hyp3/compare/v1.1.7...v2.0.0)
### Changed
- Removed `connexion` library due to inactivity, replaced with `open-api-core`
- Error messages from invalid input according to the `api-spec` are different

## [1.1.7](https://github.com/ASFHyP3/hyp3/compare/v1.1.6...v1.1.7)
### Fixed
- POST `/jobs` no longer throws 500 for`decimal.Inexact` errors, fixes [#444](https://github.com/ASFHyP3/hyp3/issues/444)
- `start_exectuion.py` will now submit at most 400 step function executions per run. Resolves an issue where no
  executions would be started when many PENDING jobs were available for submission.

## [1.1.6](https://github.com/ASFHyP3/hyp3/compare/v1.1.5...v1.1.6)
### Changed
- Landsat and Sentinel-2 autoRIFT jobs will utilize 1/3 less memory

## [1.1.5](https://github.com/ASFHyP3/hyp3/compare/v1.1.4...v1.1.5)
### Added
- Exposed new `include_wrapped_phase` API parameter for INSAR_GAMMA jobs

## [1.1.4](https://github.com/ASFHyP3/hyp3/compare/v1.1.3...v1.1.4)
### Added
- Exposed new `include_dem` API parameter for INSAR_GAMMA jobs

## [1.1.3](https://github.com/ASFHyP3/hyp3/compare/v1.1.2...v1.1.3)
### Changed
- RTC_GAMMA jobs now use the Copernicus DEM by default
- AUTORIFT jobs now accept Landsat 8 scenes with a sensor mode of ORI-only (`LO08`)

## [1.1.2](https://github.com/ASFHyP3/hyp3/compare/v1.1.1...v1.1.2)
### Added
- INSAR_GAMMA jobs now expose `include_inc_map` parameter that allows users to include an incidence angle map.

## Fixed
- Updated API GATEWAY payload format to version 2.0 to support later versions of serverless wsgi

## [1.1.1](https://github.com/ASFHyP3/hyp3/compare/v1.1.0...v1.1.1)
### Changed
- Granules for INSAR_GAMMA jobs are now validated against Copernicus GLO-30 Public DEM coverage

### Fixed
- resolved `handlers.get_names_for_user` error when `dynamo.query_jobs` requires paging.
- Resolved HTTP 500 error when quota check requires paging.

## [1.1.0](https://github.com/ASFHyP3/hyp3/compare/v1.0.0...v1.1.0)
### Added
- Exposed new `dem_name` api parameter for RTC_GAMMA jobs
  - `dem_name="copernicus"` will use the [Copernicus GLO-30 Public DEM](https://registry.opendata.aws/copernicus-dem/)
  - `dem_name="legacy"` will use the DEM with the best coverage from ASF's legacy SRTM/NED data sets

### Changed
- `util.get_job_count_for_month` now uses `Select='COUNT'` for better performance querying DynamoDB

### Changed
- Granules for RTC_GAMMA jobs are now validated against the appropriate DEM coverage map based on the value of the
  `dem_name` job parameter

## [1.0.0](https://github.com/ASFHyP3/hyp3/compare/v0.8.17...v1.0.0)
### Added
- `GET /jobs` now pages results. Large queries (that require paging) will contain a `next`
  key in the root level of the json response with a URL to fetch subsequent pages
- `GET /jobs` now accepts a `job_type` query parameter
- `GET /jobs` now provides jobs sorted by `request_time` in descending order

## [0.8.17](https://github.com/ASFHyP3/hyp3/compare/v0.8.16...v0.8.17)
### Added
- Exposed new `include_rgb` api parameter for RTC_GAMMA jobs

## [0.8.16](https://github.com/ASFHyP3/hyp3/compare/v0.8.15...v0.8.16)
### Changed
- `get_files.py` now only includes product files ending in `.zip` or `.nc` in the `files` list returned
  in `GET /jobs` API responses

## [0.8.15](https://github.com/ASFHyP3/hyp3/compare/v0.8.14...v0.8.15)
### Changed
- S3 content bucket now allows public `s3:ListBucket` and `s3:GetObjectTagging`

## [0.8.14](https://github.com/ASFHyP3/hyp3/compare/v0.8.13...v0.8.14)
### Added
- Jobs now include a `logs` key containing a list of log file download urls

## [0.8.13](https://github.com/ASFHyP3/hyp3/compare/v0.8.12...v0.8.13)
### Changed
- Increased max capacity for compute environment to 1600 vCPUs

## [0.8.12](https://github.com/ASFHyP3/hyp3/compare/v0.8.11...v0.8.12)
### Changed
- Improved response latency when submitting new jobs via `POST /jobs`

## [0.8.11](https://github.com/ASFHyP3/hyp3/compare/v0.8.10...v0.8.11)
### Added
- `GET /jobs` responses now include `s3.bucket` and `s3.key` entries for each file to facilitate interacting with
  products using s3-aware tools.

### Fixed
- AUTORIFT jobs now correctly accept Sentinel-2 granules using Earth Search IDs of 23 characters.

## [0.8.10](https://github.com/ASFHyP3/hyp3/compare/v0.8.9...v0.8.10)
### Added
- AutoRIFT jobs now allow submission with Landsat 8 Collection 2 granules

### Changed
- AutoRIFT jobs now only accept Sentinel-2 L1C granules, rather than any Sentinel-2 granules

### Removed
- API responses are no longer validated against the OpenAPI schema.  `GET /jobs` requests for jobs
  with legacy parameter values (e.g. S2 L2A granules) will no longer return HTTP 500 errors.

## [0.8.9](https://github.com/ASFHyP3/hyp3/compare/v0.8.8...v0.8.9)
### Changed
- INSAR_GAMMA jobs now use the [hyp3-gamma](https://github.com/ASFHyP3/hyp3-gamma) plugin to do processing

## [0.8.8](https://github.com/ASFHyP3/hyp3/compare/v0.8.7...v0.8.8)
### Changed
- RTC_GAMMA jobs now use the [hyp3-gamma](https://github.com/ASFHyP3/hyp3-gamma) plugin to do processing

## [0.8.7](https://github.com/ASFHyP3/hyp3/compare/v0.8.6...v0.8.7)
### Added
- Autorift jobs now allow submission with Sentinel 2 granules

## [0.8.6](https://github.com/ASFHyP3/hyp3/compare/v0.8.5...v0.8.6)
### Added
- A new `include_scattering_area` paramter has been added for `RTC_GAMMA` jobs, which includes a GeoTIFF of scattering area in the product package. This supports creation of composites of RTC images using Local Resolution Weighting per Small (2012) https://doi.org/10.1109/IGARSS.2012.6350465.
- Cloudwatch request metrics are now enabled for the S3 content bucket

## [0.8.5](https://github.com/ASFHyP3/hyp3/compare/v0.8.4...v0.8.5)
### Changed
- Api Gateway access logs are now in JSON format for easier parsing by Cloudwatch Insights
- Api Gateway access logs now include `responseLatency` and `userAgent` fields.  Unused `caller` and `userId` fields are no longer included.

## [0.8.4](https://github.com/ASFHyP3/hyp3/compare/v0.8.3...v0.8.4)
### Changed
- `/` now redirects to `/ui`

## [0.8.3](https://github.com/ASFHyP3/hyp3/compare/v0.8.2...v0.8.3)
### Changed
- Increased compute to allow 200 concurrent instances.

## [0.8.2](https://github.com/ASFHyP3/hyp3/compare/v0.8.1...v0.8.2)
### Changed
- Refactored dynamodb interactions
  - `dynamo.py` in the api code now manages all dynamodb interactions for the api
  - added tests for new dynamo module
  - added paging for dynamodb query calls

## [0.8.1](https://github.com/ASFHyP3/hyp3/compare/v0.8.0...v0.8.1)
### Added
- Added Code of Conduct and Contributing Guidelines

### Changed
- `MonthlyJobQuotaPerUser` stack parameter no longer has a default, and the value can now be set to zero.
  - Value is now set to `200` for ASF deployments.
  - Value is now set to `0` for the autoRIFT deployment.
- `POST /jobs` requests now allow up to 200 jobs per request, up from 25

## [0.8.0](https://github.com/ASFHyP3/hyp3/compare/v0.7.5...v0.8.0)
### Added
- User table which can be used to add custom quotas for users, users not in the table will still have the default.
- GET /jobs/{job_id} API endpoint to search for a job by its job_id

## [0.7.5](https://github.com/ASFHyP3/hyp3/compare/v0.7.4...v0.7.5)
### Added
- Api and processing errors will now post to a SNS topic

### Changed
* Parameters for `INSAR_GAMMA` jobs have been updated to reflect hyp3-insar-gamma [v2.2.0](https://github.com/ASFHyP3/hyp3-insar-gamma/blob/develop/CHANGELOG.md#220).

## [0.7.4](https://github.com/ASFHyP3/hyp3/compare/v0.7.3...v0.7.4)
### Changed
- API behavior for different job types is now defined exclusively in `job_types.yml`.  Available parameter types must still be defined in `apps/api/src/hyp3_api/api-sec/job_parameters.yml.j2`, and available validation rules must still be defined in `apps/api/src/hyp3_api/validation.py`.

## [0.7.3](https://github.com/ASFHyP3/hyp3/compare/v0.7.2...v0.7.3)
### Changed
- Added `AmazonS3ReadOnlyAccess` permission to batch task role to support container jobs fetching input data from S3.

## [0.7.2](https://github.com/ASFHyP3/hyp3/compare/v0.7.1...v0.7.2)
### Fixed
- RTC_GAMMA jobs now use the user-provided value for the speckle filter parameter.  Previously, the user-provided value was ignored and all jobs processed using the default value (false).

## [0.7.1](https://github.com/ASFHyP3/hyp3/compare/v0.7.0...v0.7.1)
### Changed
- Hyp3 now uses jinja templates in defining CloudFormation templates and the StepFunction definition, rendered at buildtime.
- Job types are now defined only in the API spec and the `job_types.yml` file, no job specific information needs to be added to AWS resource definitions.
- Static Analysis now requires rendering before run.

## [0.7.0](https://github.com/ASFHyP3/hyp3/compare/v0.6.1...v0.7.0)
### Added
- Added a new `AUTORIFT` job type for processing a pair of Sentinel-1 SLC IW scenes using [autoRIFT](https://github.com/leiyangleon/autoRIFT). For details, refer to the [hyp3-autorift](https://github.com/ASFHyP3/hyp3-autorift) plugin repository.

### Changed
- Updated readme deployment instructions.
- Clarified job parameter descriptions in OpenAPI specification.
- Moved step function definition into it's own file and added static analysis on step funciton definition.
- Split OpenAPI spec into multiple files using File References to resolve, static analysis change from openapi-spec-validator to prance.

## [0.6.1](https://github.com/ASFHyP3/hyp3/compare/v0.6.0...v0.6.1)
### Added
- `GET /user` response now includes a `job_names` list including all distinct job names previously submitted for the current user

### Changed
- API is now deployed using Api Gateway V2 resources, resulting in lower response latency.

## [0.6.0](https://github.com/ASFHyP3/hyp3/compare/v0.5.1...v0.6.0)
### Added
- Added a new `INSAR_GAMMA` job type for producing an interferogram from a pair of Sentinel-1 SLC IW scenes using [GAMMA](https://www.gamma-rs.ch/software).  For details, refer to the [hyp3-insar-gamma](https://github.com/ASFHyP3/hyp3-insar-gamma) plugin repository.

### Changed
- All job types requiring one or more granules now expose a single `granules` job parameter, formatted as a list of granule names:
  - `"granules": ["myGranule"]` for `RTC_GAMMA` jobs
  - `"granules": ["granule1", "granule2"]` for `INSAR_GAMMA` jobs

  Note this is a breaking change for `RTC_GAMMA` jobs.
- Browse and thumbnail URLs for `RTC_GAMMA` jobs will now be sorted with the amplitude image first, followed by the rgb image, in `GET /jobs` responses.

## [0.5.1](https://github.com/ASFHyP3/hyp3/compare/v0.5.0...v0.5.1)
### Fixed
- Resolved HTTP 500 error when submitting jobs with a resolution with decimal precision (e.g. `30.0`)

## [0.5.0](https://github.com/ASFHyP3/hyp3/compare/v0.4.0...v0.5.0)
### Changed
- The `dem_matching`, `speckle_filter`, `include_dem`, and `include_inc_map` api parameters are now booleans instead of strings.
- The `resolution` api parameter is now a number instead of a string, and the `10.0` option has been removed.

## [0.4.0](https://github.com/ASFHyP3/hyp3/compare/v0.3.9...v0.4.0)
### Changed
- Implemented 0.15° buffer and 20% threshold in DEM coverage checks when submitting new jobs.  As a result slightly more granules will be rejected as having insufficient coverage.

### Removed
- Removed optional `description` field for jobs

## [0.3.9](https://github.com/ASFHyP3/hyp3/compare/v0.3.8...v0.3.9)
### Added
- Unit tests for `get-files` lambda function

### Fixed
- Resolved HTTP 500 errors for `POST /jobs` requests when the optional `validate_only` parameter was not provided
- Jobs encountering unexpected errors in the `get-files` step will now correctly transition to a `FAILED` status

## [0.3.8](https://github.com/ASFHyP3/hyp3/compare/v0.3.7...v0.3.8)
### Added
- `POST /jobs` now accepts a `validate_only` key at root level, set to true to skip submitting jobs but run api validation.

## [0.3.7](https://github.com/ASFHyP3/hyp3/compare/v0.3.6...v0.3.7)
### Fixed
- `get-files` get expiration only from product

## [0.3.6](https://github.com/ASFHyP3/hyp3/compare/v0.3.5...v0.3.6)
### Fixed
- `get-files` step functions AMI roles for tags

## [0.3.5](https://github.com/ASFHyP3/hyp3/compare/v0.3.4...v0.3.5)
### Added
- `POST /jobs` now accepts custom job parameters when submitting jobs
- `GET /jobs` now shows parameters job was run with

### Changed
- `get_files.py` now uses tags to identify file_type instead of path

## [0.3.4](https://github.com/ASFHyP3/hyp3/compare/v0.3.3...v0.3.4)
### Added
- Name field to job parameter, set in the same way as description but with max length of 20

## [0.3.3](https://github.com/ASFHyP3/hyp3/compare/v0.3.2...v0.3.3)
### Added
- Administrators can now shut down Hyp3-api by setting SystemAvailable flag to false in CloudFormation Template and deploying

## [0.3.2](https://github.com/ASFHyP3/hyp3/compare/v0.3.1...v0.3.2)
### Added
- Retry policies to improve reliability

### Changed
- POST /jobs now accepts GRDH Files in the IW beam mode.
- Removed scaling rules and moved to MANAGED compute environment to run jobs

## [0.3.1](https://github.com/ASFHyP3/hyp3/compare/v0.3.0...v0.3.1)
### Added
- POST /jobs now checks granule intersects DEM Coverage map to provide faster feedback on common error cases
### Fixed
- Resolved bug not finding granules when submitting 10 unique granules in a RTC_GAMMA job

## [0.3.0](https://github.com/ASFHyP3/hyp3/compare/v0.2.0...v0.3.0)
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

## [0.2.0](https://github.com/ASFHyP3/hyp3/compare/v0.1.0...v0.2.0)
### Added
- New GET /user API endpoint to query job quota and jobs remaining
- browse image key for each job containing a list of urls for browse images
- browse images expire at the same time as products
- thumbnail image key for each job containing a list of urls for thumbnail images
- thubnail images expire at the same time as products

## [0.1.0](https://github.com/ASFHyP3/hyp3/compare/v0.0.0...v0.1.0)
### Added
- API checks granule exists in CMR and rejects jobs with granules that are not found
