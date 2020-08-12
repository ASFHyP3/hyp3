# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


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
