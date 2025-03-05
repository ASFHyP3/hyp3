# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [9.5.3]

### Fixed
- When the API returns an error for a `INSAR_ISCE_BURST` job because the reference and secondary scenes have different polarizations, the error message now always includes the requested polarizations in the same order as the requested scenes (previously, the order of the polarizations was not guaranteed). For example, passing a reference scene with `VV` polarization and a secondary scene with `HH` polarization results in the error message `The requested scenes need to have the same polarization, got: VV, HH`.
- The API validation behavior for the `INSAR_ISCE_MULTI_BURST` job type is now more closely aligned with that of the underlying [HyP3 ISCE2 v2.1.4](https://github.com/ASFHyP3/hyp3-isce2/releases/tag/v2.1.4) container. Currently, this only affects the `hyp3-multi-burst-sandbox` deployment.
- The reference and secondary scene names are now validated *before* DEM coverage for both `INSAR_ISCE_BURST` and `INSAR_ISCE_MULTI_BURST`.

## [9.5.2]

### Added
- The `ARIA_S1_GUNW` job type is now available in the hyp3-edc-prod deployment.

### Changed
- OPERA-DIST-S1 runtime increases from 3 to 6 hours for experimentation.
- Updated the DIST-S1 entrypoint of the image and changed the job spec accordingly.

### Fixed
- OPERA-DIST-S1 job spec had wrong CLI interface (e.g. --n-lookbacks should be --n_lookbacks).

## [9.5.1]

### Added
- `OPERA_DIST_S1` job type to all ARIA Tibet and NISAR JPL deployments.
- Stood up a new `hyp3-tibet-jpl-test` deployment for the ARIA Tibet project at JPL.

### Changed
- Increased throughput for `hyp3-cargill` (640 -> 1600 vCPUs) to support their processing needs.

### Removed
- Removed the `hyp3-enterprise-test` deployment.

## [9.5.0]

### Added
- `ARIA_S1_GUNW` job type to hyp3-edc-uat deployment.
- All jobs now have `sns:Publish` permissions for SNS topics in the same AWS region and account for the purpose of sending messages to a co-located deployment of <https://github.com/ASFHyP3/ingest-adapter>.

### Changed
- The reserved `bucket_prefix` job spec parameter has been renamed to `job_id` and can be referenced as `Ref::job_id` within each step's `command` field.
- The `job_id` parameter of the `ARIA_RAIDER` job type has been renamed to `gunw_job_id`.
- The `AUTORIFT_ITS_LIVE` job type now accepts Sentinel-1 burst products.
- `ruff` now checks for incorrect docstrings (missing docstrings are still allowed), incomplete type annotations (missing annotations are still allowed), and opportunities to use `pathlib`.
- Cloudformation parameter overrides are now provided via a .json file input to the `deploy-hyp3` GitHub action.
- The `OriginAccessIdentityId` used in EDC deployments has been renamed to `BucketReadPricipals` and now accepts multiple values.

## [9.4.0]

### Changed
- The `OPERA_DISP_TMS` job type is now a fan-out/fan-in workflow.

### Fixed
- Previously there was a bug in which fan-out job steps, defined using the `map: for item in items` syntax, would fail if `items` was an array of non-string values, because AWS Batch SubmitJob expects string parameters. This bug has been fixed by converting each value to a string before passing it to SubmitJob.

## [9.3.0]

### Added
- Added `velocity` option for the `tile_type` parameter of `OPERA_DISP_TMS` jobs
- Restored previously deleted `hyp3-opera-disp-sandbox` deployment
- Added validator to check that bounds provided do not exceed maximum size for SRG jobs

### Removed
- Removed default bounds option for SRG jobs

## [9.2.0]

### Added
- Add `mypy` to [`static-analysis`](.github/workflows/static-analysis.yml) workflow
- `OPERA_DISP_TMS` job type is now available in EDC UAT deployment

### Changed
- Upgrade to Python 3.13

### Removed
- Remove `hyp3-opera-disp-sandbox` deployment

## [9.1.1]

### Changed
- The [`static-analysis`](.github/workflows/static-analysis.yml) Github Actions workflow now uses `ruff` rather than `flake8` for linting.

## [9.1.0]

### Added
- Add a new <https://hyp3-opera-disp-sandbox.asf.alaska.edu> deployment with an `OPERA_DISP_TMS` job type for generating tilesets for the OPERA displacement tool.

## [9.0.1]

### Changed
- Upgrade to Amazon Linux 2023 AMI for Earthdata Cloud deployments

## [9.0.0]

### Changed
- All failed jobs now have a `processing_times` value of `null`.

### Fixed
- Resolve a regression introduced by the previous release (v8.0.0) in which a processing step could report a negative processing time if the underlying AWS Batch job had a failed attempt that did not include a `StartedAt` field. Fixes <https://github.com/ASFHyP3/hyp3/issues/2485>
- Upgrade from Flask v2.2.5 to v3.0.3. Fixes <https://github.com/ASFHyP3/hyp3/issues/2491>
- Specify our custom JSON encoder by subclassing `flask.json.provider.JSONProvider`. See <https://github.com/pallets/flask/pull/4692>

## [8.0.0]

### Added
- A job step can now be applied to every item in a list using a new `map: for <item> in <items>` syntax. For example, given a job spec with a `granules` parameter, a step that includes a `map: for granule in granules` field is applied to each item in the `granules` list and can refer to `Ref::granule` within its `command` field.
- If a job contains a `map` step, the processing time value for that step (in the `processing_times` list in the job's API response) is a sub-list of processing times for the step's iterations, in the same order as the items in the input list.
- A new `SRG_TIME_SERIES` job type has been added to the `hyp3-lavas` and `hyp3-lavas-test` deployments. This workflow uses the new `map` syntax described above to produce a GSLC for each level-0 Sentinel-1 granule passed via the `granules` parameter and then produces a time series product from the GSLCs. See the [HyP3 SRG](https://github.com/ASFHyP3/hyp3-srg) plugin.
- The `SRG_GSLC` job type now includes parameter validation.

### Changed
- Changes to custom compute environments:
  - Custom compute environments are now applied to individual job steps rather than to entire jobs. The `compute_environment` field is now provided at the step level rather than at the top level of the job spec.
  - If the value of the `compute_environment` field is `Default`, then the step uses the deployment's default compute environment. Otherwise, the value must be the name of a custom compute environment defined in `job_spec/config/compute_environments.yml`.
- Other changes to the job spec syntax:
  - The `tasks` field has been renamed to `steps`.
  - Job parameters no longer contain a top-level `default` field. The `default` field within each parameter's `api_schema` mapping is still supported.
  - Job specs no longer explicitly define a `bucket_prefix` parameter. Instead, `bucket_prefix` is automatically defined and can still be referenced as `Ref::bucket_prefix` within each step's `command` field.

## [7.12.0]

### Changed
- The `hyp3-its-live` deployment now uses a greater variety of `r6id[n]` instances.

## [7.11.0]

### Added
- The `INSAR_ISCE_BURST` job type is now available in the `hyp3-avo`, `hyp3-bgc-engineering`, `hyp3-cargill`, abd `hyp3-carter` deployments.
- The `AUTORIFT` job type is now available in the `hyp3-bgc-engineering`, `hyp3-cargill`, abd `hyp3-carter` deployments.

## [7.10.0]

### Added
- Added a new `INSAR_ISCE_MULTI_BURST` job type for running multi-burst InSAR. Currently, this job type is restricted to a special `hyp3-multi-burst-sandbox` deployment for HyP3 operators. However, this is an important step toward eventually making multi-burst InSAR available for general users.

### Changed
- Job validator functions now accept two parameters: the job dictionary and the granule metadata.
- Granule metadata validation now supports `reference` and `secondary` job parameters in addition to the existing `granules` parameter.
- Burst InSAR validators now support multi-burst jobs.
- Replaced the step function's `INSPECT_MEMORY_REQUIREMENTS` step with a new `SET_BATCH_OVERRIDES` step, which calls a Lambda function to dynamically calculate [Batch container overrides](https://docs.aws.amazon.com/batch/latest/APIReference/API_ContainerOverrides.html) based on job type and parameters.

## [7.9.3]
### Fixed
- Added missing cloudformation:DeleteStack permission to cloudformation deployment role in ASF-deployment-ci-cf.yml .

## [7.9.2]

### Removed
- Deleted the `hyp3-pdc` deployment in preparation for archiving the [hyp3-flood-monitoring](https://github.com/ASFHyP3/hyp3-flood-monitoring) project.

### Fixed
- Copied cloudformation permissions from user to cloudformation deployment role in ASF-deployment-ci-cf.yml to address
  breaking AWS IAM change when deploying nested stacks via a cloudformation role.

## [7.9.1]

### Changed
- The `SRG_GSLC` job now takes in a `--bounds` argument that determines the extent of the DEM used in back projection.

## [7.9.0]

### Changed
- The `ARIA_AUTORIFT.yml` job spec now specifies the optimum number of OpenMP threads and uses a dedicated compute environment with `r6id[n]` spot instances.
- The `AUTORIFT_ITS_LIVE.yml` job spec now specifies the optimum number of OpenMP threads.
- The `INSAR_ISCE.yml` job spec now reserved 16 GB memory for running the DockerizedTopsApp task.
- The `hyp3-a19-jpl-test`, `hyp3-a19-jpl`, `hyp3-tibet-jpl`, and `hyp3-nisar-jpl` ARIA deployments now uses on-demand `m6id[n]` instances.
- The `hyp3-its-live-test` deployment now uses a greater variety of `r6id[n]` instances.

## [7.8.1]

### Fixed
- Upgraded to flask-cors v5.0.0 from v4.0.1. Resolves [CVE-2024-6221](https://github.com/ASFHyP3/hyp3/security/dependabot/17).

## [7.8.0]

### Added
- Allow overriding certain AWS Batch compute environment parameters (including instance types and AMI) within a job spec.
- Allow job spec tasks to require GPU resources.

### Changed
- The `SRG_GSLC` job type now runs within a GPU environment.
- Revert ARIA hyp3 deployments back to C-instance family - including the job-spec CLI parameter `omp-num-threads` to ensure multiple jobs fit on single instance.
- Deployments with INSAR_ISCE.yml job specs will now use a dedicated compute environment with on-demand instances instead of spot instances for INSAR_ISCE jobs.

## [7.7.2]

### Change
- Renamed the `SRG_GSLC_CPU` job to `SRG_GSLC`
- Changed the `SRG_GSLC` job to use the `hyp3-srg` image, rather than `hyp3-back-projection` since the repository was renamed.


## [7.7.1]

### Removed
- The `ESA_USERNAME` and `ESA_PASSWORD` secrets have been removed from the job specs that no longer require them (those that use the `hyp3-gamma`, `hyp3-isce2`, `hyp3-autorift`, or `hyp3-back-projection` images).


## [7.7.0]

### Added
- `ARIA_AUTORIFT.yml` job spec for Solid Earth offset tracking in the ARIA JPL deployments

### Changed
- Increased throughput for `hyp3-a19-jpl` (0 -> 4,000 vCPUs) to support continued processing of ARIA GUNW products.
- The `hyp3-a19-jpl` and `hyp3-nisar-jpl` deployments now use the `m6id[n]` instance families to reduce the high number of spot interruptions seen with wth `c6id` instance family.
- Increased available vCPUs for DAAC deployments.

### Removed
- The `INSAR_ISCE_TEST.yml` job spec, which only differed from `INSAR_ISCE.yml` in support of different instance families, has been removed now that all ARIA JPL deployments are using the same instance families again.


## [7.6.0]

### Changed
- Reduced throughput for `hyp3-its-live` to prevent Sentinel-2 processing from being rate limited (10,000 -> 2,000 vCPUs).

## [7.5.0]

### Added
* The `SRG_GSLC_CPU` job spec
* The `SRG_GSLC_CPU` job type to the `hyp3-lavas` and `hyp3-lavas-test` HyP3 deployments

### Changed
- The `hyp3-tibet-jpl` deployment now uses the `m6id[n]` instance families and includes the `ARIA_RAIDER` job spec

## [7.4.0]

### Added
* The `hyp3-lavas` and `hyp3-lavas-test` enterprise HyP3 deployments.

## [7.3.0]

This release adds support for access codes. If a user specifies an active access code when they apply for HyP3 access, they will be granted automatic approval without the need for a HyP3 operator to review their application.

If you operate a HyP3 deployment, you can create a new access code by adding an item to the `AccessCodesTable` DynamoDB table for your deployment, with any string for the `access_code` attribute and an ISO-formatted UTC timestamp for the `start_date` and `end_date` attributes, e.g. `2024-06-01T00:00:00+00:00` and `2024-06-02T00:00:00+00:00` for an access code that becomes active on June 1, 2024 and expires on June 2, 2024.

### Added
- The `PATCH /user` endpoint now includes an optional `access_code` parameter and returns a `403` response if given an invalid or inactive access code.

### Changed
- Turn off hyp3 ACCESS spend by zeroing the max VCPUs in the associated deployment.
- Reduce product lifetime in hyp3 ACCESS deployment to 14 days.

## [7.2.1]

### Fixed
- Added missing `requests` dependency to lib/dyanmo/setup.py. Fixes [#2269](https://github.com/ASFHyP3/hyp3/issues/2269).

## [7.2.0]

This release includes changes to support an upcoming user whitelisting feature. A new user will be required to apply for HyP3 access and will not be able to submit jobs until an operator has manually reviewed and approved the application. As of this release, all new and existing users are automatically approved without being required to submit an application, but this will change in the near future.

⚠️ Important notes for HyP3 deployment operators:
- Changing a user's application status (e.g. to approve or reject a new user) requires manually updating the value of the `application_status` field in the Users table.
- The response for both `/user` endpoints now automatically includes all Users table fields except those prefixed by an underscore (`_`).
- The following manual updates must be made to the Users table upon deployment of this release:
  - Add field `application_status` with the appropriate value for each user.
  - Rename field `month_of_last_credits_reset` to `_month_of_last_credit_reset`.
  - Rename field `notes` to `_notes`.

### Added
- A new `PATCH /user` endpoint with a single `use_case` parameter allows the user to submit an application or update a pending application. The structure for a successful response is the same as for `GET /user`.
- A new `default_application_status` deployment parameter specifies the default status for new user applications. The parameter has been set to `APPROVED` for all deployments.

### Changed
- The `POST /jobs` endpoint now returns a `403` response if the user has not been approved.
- The response schema for the `GET /user` endpoint now includes:
  - A required `application_status` field representing the status of the user's application: `NOT_STARTED`, `PENDING`, `APPROVED`, or `REJECTED`.
  - An optional `use_case` field containing the use case submitted with the user's application.
  - An optional `credits_per_month` field representing the user's monthly credit allotment, if different from the deployment default.

### Removed
- The `reset_credits_monthly` deployment parameter has been removed. Credits now reset monthly in all deployments. This only changes the behavior of the `hyp3-enterprise-test` deployment.

## [7.1.1]
### Changed
- Reduced `start_execution_manager` batch size from 600 jobs to 500 jobs. Fixes [#2241](https://github.com/ASFHyP3/hyp3/issues/2241).

## [7.1.0]
### Added
- A `hyp3-its-live-test` deployment to [`deploy-enterprise-test.yml`](.github/workflows/deploy-enterprise-test.yml) for ITS_LIVE testing in preparation for some significant ITS_LIVE project development
- A `hyp3-a19-jpl-test` deployment to [`deploy-enterprise-test.yml`](.github/workflows/deploy-enterprise-test.yml) for ARIA testing of the `m6id[n]` instance families
- An `ARIA_RAIDER` job spec that allows RAIDER processing of previous INSAR_ISCE job that either did not include a weather model or failed on the RAiDER step.
- `ARIA_RAIDER` jobs are now available in the `hyp3-a19-jpl` and `hyp3-a19-jpl-test` deployments.

### Changed
- The `INSAR_ISCE_TEST.yml` job spec now only differs from the `INSAR_ISCE.yml` with respect to the `++omp-num-threads` parameter, because the value is specific to a particular instance family
- Job specs are no longer required to include the `granules` parameter.

### Removed
- The `AUTORIFT_ITS_LIVE_TEST.yml` job spec which supported running test versions of the AUTORIFT jobs in the production hyp3-its-live deployment

## [7.0.0]

This release marks the final transition to the new credits system. These changes apply to the production HyP3 API at <https://hyp3-api.asf.alaska.edu>. Read the [announcement](https://hyp3-docs.asf.alaska.edu/using/credits/) for full details.

### Changed

- Each type of job now costs a different number of credits, as shown in the table [here](https://hyp3-docs.asf.alaska.edu/using/credits/).
- Users are now given an allotment of 10,000 credits per month.

## [6.5.1]

### Fixed
- Added a Lambda function that sets `Private DNS names enabled` to false for VPC endpoint in EDC.

## [6.5.0]

### Added
- A `publish_bucket` parameter to `AUTORIFT_ITS_LIVE` and `AUTORIFT_ITS_LIVE_TEST` that specifies if product should be uploaded to either the ITS_LIVE open data bucket or test bucket.
- Access key secrets to `AUTORIFT_ITS_LIVE` and `AUTORIFT_ITS_LIVE_TEST` that allow for S3 upload of products.

### Changed
- Update throughput for ACCESS deployments by factor of 4 (from 1000 to 4000 vcpus).

## [6.4.0]

### Changed
- Reduced vcpu limits for EDC deployments from 1,500/3,000 to 1,200/2,400.

### Removed
- The `disable-private-dns` lambda function added in v4.3.2 has been removed; the underlying issue has been resolved in
  the Earthdata Cloud platform. Fixes [#1956](https://github.com/ASFHyP3/hyp3/issues/1956).

## [6.3.0]

### Changed
- `/costs` API endpoint now returns a list of job cost dictionaries, instead of a dictionary of dictionaries.
- Cost table parameters are now contained within the `parameter_value` dictionary key.
- Cost table costs are now contained within the `cost` dictionary key.

## [6.2.0]

HyP3 is in the process of transitioning from a monthly job quota to a credits system. [HyP3 v6.0.0](https://github.com/ASFHyP3/hyp3/releases/tag/v6.0.0) implemented the new credits system without changing the number of jobs that users can run per month. This release implements the capability to assign a different credit cost to each type of job, again without actually changing the number of jobs that users can run per month.

Beginning on April 1st, the production API at <https://hyp3-api.asf.alaska.edu> will assign a different cost to each type of job and users will be given an allotment of 10,000 credits per month. Visit the [credits announcement page](https://hyp3-docs.asf.alaska.edu/using/credits/) for full details.

### Added
- `/costs` API endpoint that returns a table that can be used to look up the credit costs for different types of jobs.

### Changed
- The <https://hyp3-test-api.asf.alaska.edu> API now implements the credit costs displayed on the [credits announcement page](https://hyp3-docs.asf.alaska.edu/using/credits/).
- `hyp3-a19-jpl` and `hyp3-tibet-jpl` deployments max vCPUs have been reduced to 1,000 from 10,000 because of persistent spot interruptions.

## [6.1.1]

### Changed
- Upgraded to `cryptography==42.0.4`. Fixes CVE-2024-26130.

## [6.1.0]

### Added
- Previously, the `job_parameters` field of the `job` object returned by the `/jobs` API endpoint only included parameters whose values were specified by the user. Now, the field also includes optional, unspecified parameters, along with their default values. This does not change how jobs are processed, but gives the user a complete report of what parameters were used to process their jobs.

### Changed
- Increased maximum vCPUs from 0 to 10,000 in the hyp3-tibet-jpl deployment.
- Decreased product lifetime from 60 days to 30 days in the hyp3-tibet-jpl deployment.

## [6.0.0]

HyP3's monthly quota system has been replaced by a credits system. Previously, HyP3 provided each user with a certain number of jobs per month. Now, each job costs a particular number of credits, and users spend credits when they submit jobs. This release assigns every job a cost of 1 credit, but future releases will assign a different credit cost to each job type. Additionally, the main production deployment (`https://hyp3-api.asf.alaska.edu`) resets each user's balance to 1,000 credits each month, effectively granting each user 1,000 jobs per month. Therefore, users should not notice any difference when ordering jobs via ASF's On Demand service at <https://search.asf.alaska.edu>.

### Added
- The `job` object returned by the `/jobs` API endpoint now includes a `credit_cost` attribute, which represents the job's cost in credits.
- A `DAR` tag is now included in Earthdata Cloud deployments for each S3 bucket to communicate which contain objects
  that required to be encrypted at rest.

### Changed
- The `quota` attribute of the `user` object returned by the `/user` API endpoint has been replaced by a `remaining_credits` attribute, which represents the user's remaining credits.

### Removed
- The non-functional CloudWatch alarm for API 5xx errors has been removed from the `monitoring` module. See [#2044](https://github.com/ASFHyP3/hyp3/issues/2044).

## [5.0.4]
### Added
- `INSAR_ISCE_BURST` jobs are now available in the azdwr-hyp3 deployment.

### Changed
- Addressed breaking changes with upgrade to `moto[dynamodb]==5.0.0`

## [5.0.3]
### Fixed
- Fix how the `INSAR_ISCE_BURST` antimeridian error message is formatted.

## [5.0.2]
### Added
- A validation check for `INSAR_ISCE_BURST` that will fail if a granule crosses the antimeridian.

## [5.0.1]
### Fixed
- Upgrade the `openapi-core`, `openapi-spec-validator`, and `jsonschema` packages to their latest versions. This is now possible thanks to the pre-release of [openapi-core v0.19.0a1](https://github.com/python-openapi/openapi-core/releases/tag/0.19.0a1), which fixes <https://github.com/python-openapi/openapi-core/issues/662>. Resolves <https://github.com/ASFHyP3/hyp3/issues/1193>.

## [5.0.0]
### Removed
- `legacy` option for the `dem_name` parameter of `RTC_GAMMA` jobs. All RTC processing will now use the Copernicus DEM.
### Fixed
- The description of the INSAR_ISCE_BURST job's `apply_water_mask` to state that water masking now happens BEFORE unwrapping.

## [4.5.1]
### Fixed
- `output_resolution` in the `INSAR_ISCE_TEST` job spec is now correctly specified as an int instead of number, which can be a float or an int.

## [4.5.0]
### Changed
- Update `INSAR_ISCE` and `INSAR_ISCE_TEST` job spec for GUNW version 3+ standard and custom products
  - `frame_id` is now a required parameter and has no default
  - `compute_solid_earth_tide` and `estimate_ionosphere_delay` now default to `true`
  - `INSAR_ISCE_TEST` exposes custom `goldstein_filter_power`, `output_resolution`, `dense_offsets`, and `unfiltered_coherence` parameters

## [4.4.1]
### Changed
- Updated `WATER_MAP` job spec to point at the [HydroSAR images](https://github.com/fjmeyer/HydroSAR/pkgs/container/hydrosar)
  instead of the [ASF Tools images](https://github.com/asfhyp3/asf-tools/pkgs/container/asf-tools) as the HydroSAR code
  is being migrated to the HydroSAR project repository.

### Fixed
- Reverted the new AWS Batch job retry strategy introduced in [HyP3 v4.1.2](https://github.com/ASFHyP3/hyp3/releases/tag/v4.1.2). Fixes https://github.com/ASFHyP3/hyp3/issues/1944

### Removed
- Removed the unused `RIVER_WIDTH` job spec.
- Removed the `WATER_MAP` job spec from UAT as it's not expected to be available in HyP3 production anytime soon.

## [4.4.0]
### Added
- INSAR_ISCE_BURST job to EDC production deployment.

## [4.3.2]
### Fixed
- Added a Lambda function that sets `Private DNS names enabled` to false for VPC endpoint.

## [4.3.1]
### Added
- The `ESA_USERNAME` and `ESA_PASSWORD` secrets have been added to all of the job specs that require them.

## [4.3.0]
### Changed
- The `iterative_min_size` and `minimization_metric` parameters have been moved from the `WATER_MAP_TEST` job spec to the `WATER_MAP` job spec. The default `minimization_metric` value has been changed from `fmi` to `ts`.
- The `known_water_threshold` parameter for the `WATER_MAP` job type is now nullable, with a default value of `null` instead of `30.0` percent. A water threshold is computed when the value is `null`.
- Use Amazon Linux 2023 AMI in non-Earthdata Cloud environments
  - Reduced the memory reservation of some job types due to slightly less memory being available for AWS Batch jobs on the AL2023 AMI
- All deployments now use the `SPOT_PRICE_CAPACITY_OPTIMIZED` allocation strategy for AWS Batch. This includes JPL
  deployments, reverting the temporary change to On Demand instances in HyP3 v3.10.8
### Removed
- The `WATER_MAP_TEST` job spec

## [4.2.1]
### Changed
- The `ami_id` for EDC platforms now uses the original AMI.

## [4.2.0]
### Added
- Added `phase_filter_parameter` for `INSAR_GAMMA` job type.
### Removed
- Removed the `INSAR_GAMMA_TEST` job type from the `hyp3-avo` and `hyp3-enterprise-test` deployments, now that the `phase_filter_parameter` option is available for the `INSAR_GAMMA` job type.

## [4.1.2]
### Changed
- AWS Batch jobs are now retried twice, once after 10 minutes and once after 60 minutes, to reduce the number of jobs that fail due to transient errors, such as Earthdata Login and Sentinel-1 distribution outages.

## [4.1.1]
### Added
- New DEM coverage map that allows COP90 tiles to fill the COP30 gaps over Azerbaijan and Armenia.
### Fixed
- Pinned `Werkzeug==2.3.7` in `requirements-apps-api.txt`. Mitigates [#1861](https://github.com/ASFHyP3/hyp3/issues/1861)
  pending a fix for https://github.com/logandk/serverless-wsgi/issues/247

## [4.1.0]
### Added
- New `parameter_file` parameter for the `AUTORIFT_ITS_LIVE` and `AUTORIFT_ITS_LIVE_TEST` job types.

## [4.0.0]
### Removed
- The Subscriptions feature has been removed.
  - Removed the `/subscriptions` API endpoint.
  - Removed the `subscription_id` query parameter from the `GET /jobs` API endpoint.
  - Removed the `subscription_id` field from the response body of the `GET /jobs` API endpoint.

## [3.10.10]
### Changed
- Reduced vCPU limits for `hyp3-tibet-jpl` to 0 from 10,000.

## [3.10.9]
### Changed
- The public key for the JWT auth provider is now specified as a GitHub Secret. Fixes https://github.com/ASFHyP3/hyp3/issues/1765

## [3.10.8]
### Changed
- HyP3 deployments at JPL now use On Demand instances instead of Spot instances to prevent `INSAR_ISCE` jobs from being interrupted.
  This *should* be a temporary change.

## [3.10.7]
### Changed
- The `INSAR_ISCE_BURST` job type now validates that polarizations and burst ids are the same.

## [3.10.6]
### Changed
- Increased vCPU limits for `hyp3-a19-jpl` and `hyp3-tibet-jpl` from 1,600 to 10,000.

## [3.10.5]
### Changed
- Updated INSAR_ISCE job specification for [DockerizedTopsApp](https://github.com/ACCESS-Cloud-Based-InSAR/DockerizedTopsApp) v0.2.4
- Added larger `c6id` instance types to hyp3-a19-jpl and hyp3-nisar-jpl deployments

## [3.10.4]
### Changed
- The `hyp3-edc-uat` and `hyp3-edc-prod` deployments now uses the latest Earthdata Cloud AMI with additional software installed.

## [3.10.3]
### Changed
- Increased product lifetime for hyp3-tibet-jpl deployment from 14 days to 60 days.

## [3.10.2]
### Deprecated
- The Subscriptions feature has been deprecated and will be removed as early as `2023-09-05` (September 5, 2023).
  Please read our [Subscriptions docs](https://hyp3-docs.asf.alaska.edu/using/subscriptions/)
  for more details and **take the recommended actions to avoid data loss.**
  You can also follow our
  [Jupyter notebook tutorials](https://hyp3-docs.asf.alaska.edu/tutorials/process-new-granules-for-search-parameters/)
  to learn how to reproduce subscription-like behavior using the HyP3 SDK.

## [3.10.1]
### Changed
- Updated default public key used to verify authentication cookie

## [3.10.0]
### Added
- Added `INSAR_ISCE_BURST` job type to `hyp3-test` deployment.
### Changed
- Added larger `c6id` instance types to hyp3-tibet-jpl deployment
- Set `++omp-num-threads=4` for `INSAR_ISCE_TEST` jobs

## [3.9.8]
### Removed
- Removed `c5d.xlarge` instance types from hyp3-tibet-jpl and hyp3-nisar-jpl deployments.

## [3.9.7]
### Changed
- Added `r6idn` instance types and removed `r5d`,`r5dn` instance types from most deployments.

## [3.9.6]
### Removed
- `PermissionsBoundaryPolicyArn` stack parameter; this setting is no longer required for Earthdata Cloud deployments

## [3.9.5]
### Added
- `apply_water_mask` option for `INSAR_ISCE_BURST` jobs
### Changed
- `POST /jobs` now returns HTTP 400 for Sentinel-1 Burst granules that do not exist in CMR
- `POST /jobs` now returns HTTP 400 for INSAR_ISCE_BURST jobs for burst granules that do not intersect the
  Copernicus GLO-30 Public DEM.

## [3.9.4]
### Fixed
- Modified `start_execution_manager` to submit no more than 2 batches of 300 jobs, in order to reduce payload size.
  Fixes [#1689](https://github.com/ASFHyP3/hyp3/issues/1689).

## [3.9.3]
### Fixed
- Reduced `start-execution-worker` concurrency to address AWS Batch `Too Many Requests` errors. Fixes [#1676](https://github.com/ASFHyP3/hyp3/issues/1676).
- Added jobs query pagination for `subscription-worker` so that all jobs will be retrieved when constructing the list of processed granules.

## [3.9.2]
### Fixed
- Reverted `asf_search` to v6.0.2. Fixes [#1673](https://github.com/ASFHyP3/hyp3/issues/1673).

## [3.9.1]
### Fixed
- Invalid `install_requires` clause in `dynamo/setup.py`. Fixes [#1666](https://github.com/ASFHyP3/hyp3/issues/1666).

## [3.9.0]
### Added
- Added a new `hyp3-pdc` deployment.

## [3.8.0]
### Added
- Added `INSAR_ISCE_BURST` job spec to the `hyp3-enterprise-test` deployment.
- Added the `S1_CORRECTION_ITS_LIVE` job spec to the `hyp3-enterprise-test` and `hyp3-its-live` deployments.

### Changed
- The hyp3-autorift plugin now specifies the optimum number of OpenMP threads through the global `++omp-num-threads`
  argument

## [3.7.0]
### Added
- Added the `WATER_MAP_TEST` job spec to the `hyp3-watermap` deployment.
### Changed
- the `flood_depth_estimator` parameter in both the `WATER_MAP` and `WATER_MAP_TEST` job spec is now nullable.

## [3.6.1]
### Changed
- - Increased the `hyp3-tibet-jpl` vCPU limit from 0 to 1600.
### Removed
- The [`RIVER_WIDTH`](job_spec/RIVER_WIDTH.yml) job spec from the `hyp3-streamflow` deployment.

## [3.6.0]
### Added
- The `GET /jobs` endpoint now includes a `user_id` parameter, which allows retrieving jobs submitted by another user.
  If `user_id` is not provided, jobs are returned for the current user.
- Added the `WATER_MAP_EQ` job spec to the `hyp3-watermap` deployment.
- Added 20m resolution to the `WATER_MAP_EQ` job spec.

## [3.5.1]
### Changed
- Increased memory available to INSAR_GAMMA jobs in azdwr-hyp3 deployment.
### Fixed
- Job `status_code` field should only switch to `RUNNING` if current value is `PENDING`
  (fixes [#1539](https://github.com/ASFHyP3/hyp3/issues/1539)).

## [3.5.0]
### Added
- Added `resolution=20.0` option for `RTC_GAMMA` jobs.
- Added a [`WATER_MAP_EQ`](job_spec/WATER_MAP_EQ.yml) job spec to the `hyp3-streamflow` and `hyp3-enterprise-test`
  deployments.

## [3.4.0]
### Added
- Added `resolution=20.0` option for `WATER_MAP` jobs.

## [3.3.0]
### Added
- Added `hyp3-carter` deployment.
- An [`INSAR_GAMMA_TEST.yml`](job_spec/INSAR_GAMMA_TEST.yml) job spec  has been added, exposing the adaptive phase filter parameter used when processing InSAR products.
- `INSAR_GAMMA_TEST.yml` job spec has been added to the HyP3 Enterprise Test and HyP3 AVO deployments.

## [3.2.1]
### Changed
- Increased the `hyp3-streamflow` product lifecycle from 14 days to 90 days.
- Increased the `hyp3-streamflow` vCPU limit from 640 to 1600.

## [3.2.0]
### Added
- [`job_spec`s](job_spec/) can now specify a required set of secrets and an AWS Secrets Manage Secret ARN to pull the
  secret values from. Notably, secrets are now externally managed and not part of the HyP3 stack.

## [3.1.2]
### Added
- `INSAR_ISCE_TEST` jobs now accept an `compute_solid_earth_tide` option to compute the solid earth tide ionosphere correction layer.

## [3.1.1]
### Fixed
- `INSAR_ISCE` and `INSAR_ISCE_TEST` jobs no longer accept the unsupported `NCMR` weather model; [see RAiDER#485](https://github.com/dbekaert/RAiDER/issues/485).

## [3.1.0]
### Added
- `INSAR_ISCE_TEST` jobs now accept a `frame_id` parameter. GUNW products are subset to this frame.
- `INSAR_ISCE_TEST` jobs now accept an `estimate_ionosphere_delay` option to apply ionosphere correction.
- `INSAR_ISCE_TEST` jobs now accept an `esd_coherence_threshold` parameter to specify whether or not to perform the Enhanced Spectral Diversity (ESD), and what ESD coherence threshold to use.

## [3.0.0]
### Added
- `INSAR_ISCE` and `INSAR_ISCE_TEST` jobs now accepts all weather model parameters [allowed by `RAiDER`](https://github.com/dbekaert/RAiDER/blob/dev/tools/RAiDER/models/allowed.py).
- Added `hyp3-bgc-engineering` deployment.
### Changed
- `WATER_MAP` and `RIVER_WIDTH` jobs are now run as a series of multiple tasks.
- The `flood_depth_estimator` parameter for `WATER_MAP` jobs is now restricted to a set of possible values.
- Changed the default value for the `flood_depth_estimator` parameter for `WATER_MAP` jobs from `iterative` to `None`.
  A value of `None` indicates that a flood map will not be included.
- Reduced `ITS_LIVE` product lifetime cycle from 180 days to 45 days.
### Removed
- Removed the `include_flood_depth` parameter for `WATER_MAP` jobs.

## [2.25.0]
### Added
- `INSAR_ISCE` and `INSAR_ISCE_TEST` jobs now accept a `weather_model` parameter to specify which weather model to use
   when estimating trophospheric delay data.
- Increases the memory available to `AUTORIFT` jobs for Landsat pairs

## [2.24.0]
### Added
- Made `resolution=10.0` parameter option for RTC_GAMMA and WATER_MAP jobs available in all deployments
### Changed
- Updated hyp3-enterprise-test, hyp3-watermap, hyp3-streamflow, and hyp3-cargill deployments to include larger EC2
  instance types capable of running multiple jobs per instance.
- `INSAR_ISCE` and `INSAR_ISCE_TEST` jobs will now only accept SLC scenes with a polarization of VV or VV+VH.

## [2.23.0]
### Changed
- Set `++omp-num-threads 4` for RTC_GAMMA, INSAR_GAMMA, WATER_MAP, and AUTORIFT jobs to drastically reduce CPU
  contention when running multiple jobs on the same EC2 instance.
- Updated DAAC deployments to include larger EC2 instance types capable of running multiple jobs per instance.

## [2.22.0]
### Added
- In addition to `power` and `amplitude`, `decibel` can now be provided as the `scale` for `RTC_GAMMA` jobs

## [2.21.12]
### Added
- Added `lambda_logging` library for re-usable Lambda logging functionality.

## [2.21.11]
### Changed
- Increase vCPU and monthly budget values for test and production EDC deployments.

## [2.21.10]
### Changed
- Drop the `c5d` instance family due to disk space limitations for GUNW product generation in the ACCESS19 JPL deployment.

## [2.21.9]
### Added
- Added hyp3-cargill deployment

## [2.21.8]
### Changed
- AUTORIFT jobs for Sentinel-2 scenes can now only be submitted using ESA naming convention.

## [2.21.7]
### Changed
- Reduced hyp3-tibet-jpl deployment to 700 maximum VCPUs.

## [2.21.6]
### Added
- Included `r5d.xlarge` EC2 instances types in most deployments to improve Spot availability

## [2.21.5]
### Added
- A new `AUTORIFT_TEST` job type for the hyp3-its-live deployment running the `test` version of the container.

## [2.21.4]
### Changed
- Batches of step function executions are now started in parallel using a manager to launch one worker per batch of jobs
  (currently up to 3 batches of 300 jobs for a total of 900 jobs each time the manager runs).

## [2.21.3]
### Added
- AutoRIFT jobs now allow submission of Landsat 4, 5, and 7 Collection 2 scene pairs

## [2.21.2]
### Changed
- Subscription handling is now parallelized using a manager to launch one worker per subscription, in order to help
  prevent timeouts while handling subscriptions.

## [2.21.1]
### Changed
- Upgraded Batch compute environments to the latest generation `r6id`/`c6id` EC2 instance types

## [2.21.0]
### Added
- Added `processing_times` field to the Job schema in the API in order to support jobs with multiple processing steps.
### Removed
- Removed `processing_time_in_seconds` field from the Job schema.

## [2.20.0]
### Added
- New `RIVER_WIDTH` job type.
### Changed
- Job specifications can now specify multiple tasks.

## [2.19.7]
### Changed
- `WATER_MAP` and `WATER_MAP_10M` now can run up to 10 hours before timing out.

## [2.19.6]
### Changed
- `WATER_MAP` and `WATER_MAP_10M` now can run up to 19800s before timing out.

## [2.19.5]
### Changed
- `scale-cluster` now temporarily disables the Batch Compute Environment to allow maxvCpus to be reduced in cases when
  the current desired vCpus exceeds the new target value.

## [2.19.4]
### Changed
- `scale-cluster` now adjusts the compute environment size based on total month-to-date spending, rather than only EC2
  spending.

## [2.19.3]
### Fixed
- Granted additional IAM permissions required by AWS Step Functions to manage AWS Batch jobs.

## [2.19.2]
### Changed
- Changed the Swagger UI page header and title to reflect the particular HyP3 deployment.

## [2.19.1]
### Fixed
- The `next` URL in paginated `GET /jobs` responses will now reflect the correct API hostname and path in load balanced
  environments. Fixes [#1071](https://github.com/ASFHyP3/hyp3/issues/1071).

## [2.19.0]
### Added
- Added support for updating subscription `start` and `intersectsWith` fields.

## [2.18.1]
### Changed
- Increased `MemorySize` for `process-new-granules` function to improve performance when evaluating subscriptions.

## [2.18.0]
### Removed
- `BannedCidrBlocks` stack parameter to specify CIDR ranges that will receive HTTP 403 Forbidden responses from the API

## [2.17.5]
### Changed
- Granules for jobs are now validated against the updated [2021  release of Copernicus GLO-30 Public DEM coverage](https://spacedata.copernicus.eu/blogs/-/blogs/copernicus-dem-2021-release-now-available).

## [2.17.4]
### Added
- GitHub action to scan Python dependencies and rendered CloudFormation templates for known security vulnerabilities
  using Snyk.

## [2.17.3]
### Fixed
- AUTORIFT jobs can now be submitted for Sentinel-2 scenes with 25-character Earth Search names. Fixes [#1022](https://github.com/ASFHyP3/hyp3/issues/1022).

## [2.17.2]
### Fixed
- `GET /jobs` requests now accept `name` parameters up to 100 characters. Fixes [#1019](https://github.com/ASFHyP3/hyp3/issues/1019).

## [2.17.1]
### Fixed
- Fix how we fetch jobs that are waiting for step function execution, so that we actually start up to 400 executions at a time.
- Added default values for `logs` and `expiration_time`, which should prevent failed jobs from remaining in `RUNNING`.

## [2.17.0]
### Added
- Monthly job quota checks can now be suppressed for individual users by setting `max_jobs_per_month` to `null` in the users table.
- A user can now be given a fixed Batch job priority for all jobs that they submit by setting the `priority` field in the users table.

## [2.16.1]
### Fixed
- Handle missing log stream when uploading logs, which should prevent jobs from remaining in `RUNNING` status after failure.
- Don't write error messages to `processing_time_in_seconds` field.

## [2.16.0]
### Added
- Added `execution_started` field to job schema to indicate whether a step function execution has been started for the job.
### Changed
- Job status code doesn't switch from `PENDING` to `RUNNING` until the Batch job starts running.

## [2.15.0]
### Added
- Added flood depth options to water map job (currently limited to `hyp3-test`).
### Changed
- Increased job name length limit to 100 characters.

## [2.14.4]
### Fixed
- Compute processing time when one or more Batch attempts is missing a `StartedAt` time.

## [2.14.3]
### Fixed
- Convert floats to decimals when adding a subscription.
- Process new granules for `WATER_MAP` subscriptions.

## [2.14.2]
### Fixed
- Step function now retries the CHECK_PROCESSING_TIME task when errors are encountered.

## [2.14.1]
### Fixed
- Step function now retries transient `Batch.AWSBatchException` errors when submitting jobs to AWS Batch. Fixes [#911](https://github.com/ASFHyP3/hyp3/issues/911).

## [2.14.0]
### Added
- Expose CloudFront product download URLs for Earthdata Cloud environments via the HyP3 API.
- `OriginAccessIdentityId` stack parameter supporting content distribution via CloudFront.

## [2.13.0]
### Changed
- Upgraded AWS Lambda functions and Github Actions to Python 3.9
- Require HttpTokens to be consistent with EC2 instance metadata configured with Instance Metadata Service Version 2 (IMDSv2).
- Cloudformation stack parameters that are specific to Earthdata Cloud environments are now managed via Jinja templates,
  rather than CloudFormation conditions.

## [2.12.1]
### Added
- A `JPL-public` security environment when rendering CloudFormation templates which will
  deploy a public bucket policy. To use this environment, the AWS S3 account level Block All Public Access
  setting must have been turned off by the JPL Cloud team.

### Fixed
- The `JPL` security environment, when rendering CloudFormation templates, will no longer
  deploy a public bucket policy as this is disallowed by default for JPL commercial cloud accounts.

## [2.12.0]
### Added
- New `InstanceTypes` parameter to the cloudformation template to specify which EC2 Instance Types are available to the
  Compute Environment
- Added `r5dn.xlarge` as an eligible instance type in most HyP3 deployments

### Changed
- The `job_spec_files` positional argument to [`render_cf.py`](apps/render_cf.py) has been switched to a
  required `--job-spec-files` optional argument to support multiple open-ended arguments.
- Set S3 Object Ownership to `Bucket owner enforced` for all buckets so that access via ACLs is no longer supported.

## [2.11.0]
### Changed
- The HyP3 API is now implemented as an API Gateway REST API, supporting private API deployments.

## [2.10.0]
### Added
- AutoRIFT jobs now allow submission with Landsat 9 Collection 2 granules

## [2.9.0]
### Added
- Add `processing_time_in_seconds` to the `job` API schema to allow plugin developers to check processing time.

## [2.8.4](https://github.com/ASFHyP3/hyp3/compare/v2.8.3...v2.8.4)
### Security
- Encrypt Earthdata username and password using AWS Secrets Manager.
### Added
- Documentation about deploying to a JPL-managed commercial AWS account has been added to
  [`docs/deployments`](docs/deployments).

## [2.8.3](https://github.com/ASFHyP3/hyp3/compare/v2.8.2...v2.8.3)
### Changed
- Increase monthly job quota per user from 250 to 1,000.

## [2.8.2](https://github.com/ASFHyP3/hyp3/compare/v2.8.1...v2.8.2)
### Fixed
- Limited the number of jobs a subscription can send at a time to avoid timing out. Fixes [#794](https://github.com/ASFHyP3/hyp3/issues/794).
- Confirm there are no unprocessed granules before disabling subscriptions past their expiration date.

## [2.8.1](https://github.com/ASFHyP3/hyp3/compare/v2.8.0...v2.8.1)
### Changed
- Jobs are now assigned a `priority` attribute when submitted. `priority` is calculated based on jobs already
  submitted month-to-date by the same user. Jobs with a higher `priority` value will run before jobs with a lower value.
- `Batch.ServerException` errors encountered by the Step Function are now retried, to address intermittent errors when
  the Step Functions service calls the Batch SubmitJob API.

## [2.8.0](https://github.com/ASFHyP3/hyp3/compare/v2.7.7...v2.8.0)
### Added
- HyP3 can now be deployed into a JPL managed commercial AWS account
- Selectable security environment when rendering CloudFormation templates, which will modify resources/configurations for:
  - `ASF` (default) -- AWS accounts managed by the Alaska Satellite Facility
  - `EDC` -- AWS accounts managed by the NASA Earthdata CLoud
  - `JPL` -- AWS accounts managed by the NASA Jet Propulsion Laboratory
- A `security_environment` Make variable used by the `render` target (and any target that depends on `render`).
  Use like `make security_environment=ASF build`

### Changed
- All CloudFormation templates (`*-cf.yml`) are now rendered from jinja2 templates (`*-cf.yml.j2`)

### Removed
- The `EarthdataCloud` CloudFormation template parameter to `apps/main-cf.yml`

## [2.7.7](https://github.com/ASFHyP3/hyp3/compare/v2.7.6...v2.7.7)
### Changed
- Use Managed Policies for IAM permissions in support of future deployments using custom CloudFormation IAM resources

## [2.7.6](https://github.com/ASFHyP3/hyp3/compare/v2.7.5...v2.7.6)
### Added
- Added build target to Makefile.

## [2.7.5](https://github.com/ASFHyP3/hyp3/compare/v2.7.4...v2.7.5)
### Removed
- Disabled default encryption for the monitoring SNS topic. Fixes [#762](https://github.com/ASFHyP3/hyp3/issues/762).

## [2.7.4](https://github.com/ASFHyP3/hyp3/compare/v2.7.3...v2.7.4)
### Added
- Enabled default encryption for the monitoring SNS topic

### Changed
- Block Public Access settings for the S3 content bucket are now configured based on the EarthdataCloud stack parameter.

## [2.7.3](https://github.com/ASFHyP3/hyp3/compare/v2.7.2...v2.7.3)
### Changed
- s3 access log bucket is now encrypted using [AWS S3 Bucket Keys](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-key.html)

## [2.7.2](https://github.com/ASFHyP3/hyp3/compare/v2.7.1...v2.7.2)
### Changed
- The `scale-cluster` lambda now reduces `desiredVpucs` to match `maxVcpus` when necessary to allow the compute
  environment to scale down immediately.

## [2.7.1](https://github.com/ASFHyP3/hyp3/compare/v2.7.0...v2.7.1)
### Changed
- The `DomainName` and `CertificateArn` stack parameters are now optional, allowing HyP3 to be deployed without
  a custom domain name for the API.

## [2.7.0](https://github.com/ASFHyP3/hyp3/compare/v2.6.6...v2.7.0)
### Added
- Support for automatic toggling between two `maxvCpus` values for the Batch compute environment, based on monthly
  budget vs month-to-date spending

## [2.6.6](https://github.com/ASFHyP3/hyp3/compare/v2.6.5...v2.6.6)
### Fixed
- Api 400 responses now use a consistent JSON schema for the response body. Fixes [#625](https://github.com/ASFHyP3/hyp3/issues/625)

## [2.6.5](https://github.com/ASFHyP3/hyp3/compare/v2.6.4...v2.6.5)
### Changed
- Default autoRIFT parameter file was updated to point at the new `its-live-data` AWS S3 bucket
  instead of `its-live-data.jpl.nasa.gov`, except for the custom `autorift-eu` deployment which uses a copy in `eu-central-1`.
- Job specification YAMLs can now specify a container `image_tag`, which will override the deployment default
  image tag
- Provided example granule pairs for INSAR_GAMMA and AUTORIFT jobs in the OpenApi schema

## [2.6.4](https://github.com/ASFHyP3/hyp3/compare/v2.6.3...v2.6.4)
### Fixed
- `POST /jobs` no longer allows users to submit a job of one `job_type` with the parameters of another
- `POST /subscriptions` no longer allows user to submit a subscriptions of one `job_type` with the parameters of another
- `ProcessNewGranules` now converts `decimal.Decimal` objects to `float` or `int` before passing to `asf_search.search`

## [2.6.3](https://github.com/ASFHyP3/hyp3/compare/v2.6.2...v2.6.3)
### Fixed
- fixed typo in `search_parameteters['FlightDirection']` DECENDING -> DESCENDING

## [2.6.2](https://github.com/ASFHyP3/hyp3/compare/v2.6.1...v2.6.2)
### Added
- New `AmiId` stack parameter to specify a specific AMI for the AWS Batch compute environment

### Changed
- `job_spec/*.yml` files are now explicitly selected allowing per-deployment job customization

### Removed
- `AutoriftImage`, `AutoriftNamingScheme`, and `AutoriftParameterFile` CloudFormation stack parameters
  have been removed and are instead captured in custom `job_spec/*.yml` files.

## [2.6.1](https://github.com/ASFHyP3/hyp3/compare/v2.6.0...v2.6.1)
### Added
- Optional `DeployLambdasInVpc` stack parameter to deploy all lambda functions into the given `VpcId` and `SubnetIds`

## [2.6.0](https://github.com/ASFHyP3/hyp3/compare/v2.5.3...v2.6.0)
### Changed
- Job types now are defined each in their own file under the `job_spec` directory
- Api job parameters are now defined in the `job_spec` folder for the given job type

## [2.5.3](https://github.com/ASFHyP3/hyp3/compare/v2.5.2...v2.5.3)
### Added
- Optional `PermissionsBoundaryPolicyArn` stack parameter to apply to all created IAM roles

## [2.5.2](https://github.com/ASFHyP3/hyp3/compare/v2.5.1...v2.5.2)
### Fixed
- Resolved an issue where API requests would return HTTP 500 due to space-padded sourceIp value, e.g. ' 123.123.123.50'

## [2.5.1](https://github.com/ASFHyP3/hyp3/compare/v2.5.0...v2.5.1)
### Added
- `BannedCidrBlocks` stack parameter to specify CIDR ranges that will receive HTTP 403 Forbidden responses from the API

### Changed
- All job parameters of type `list` now are converted to space delimited strings prior to invoking job definitions in Batch.

## [2.5.0](https://github.com/ASFHyP3/hyp3/compare/v2.4.3...v2.5.0)
### Added
- Exposed new `include_displacement_maps` API parameter for INSAR_GAMMA jobs, which will cause both a line-of-sight
  displacement and a vertical displacement GEOTIFF to be included in the product.

### Changed
- Reduced default job quota to 250 jobs per user per month

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

### Fixed
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
