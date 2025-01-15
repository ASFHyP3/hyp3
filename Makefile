API = ${PWD}/apps/api/src
APPS = ${PWD}/apps
CHECK_PROCESSING_TIME = ${PWD}/apps/check-processing-time/src
GET_FILES = ${PWD}/apps/get-files/src
HANDLE_BATCH_EVENT = ${PWD}/apps/handle-batch-event/src
SET_BATCH_OVERRIDES = ${PWD}/apps/set-batch-overrides/src
SCALE_CLUSTER = ${PWD}/apps/scale-cluster/src
START_EXECUTION_MANAGER = ${PWD}/apps/start-execution-manager/src
START_EXECUTION_WORKER = ${PWD}/apps/start-execution-worker/src
DISABLE_PRIVATE_DNS = ${PWD}/apps/disable-private-dns/src
UPDATE_DB = ${PWD}/apps/update-db/src
UPLOAD_LOG = ${PWD}/apps/upload-log/src
DYNAMO = ${PWD}/lib/dynamo
AWS_PROFILE ?= default
AWS_REGION ?= us-west-2
DOCKER_TAG ?= test
IMAGE_NAME ?= hyp3_deploy
PACKAGE_CMD = aws cloudformation package \
		--template-file ./apps/main-cf.yml \
		--s3-bucket $(ARTIFACT_BUCKET_NAME) \
		--output-template-file packaged.yml \
		--profile $(AWS_PROFILE)

export PYTHONPATH = ${API}:${CHECK_PROCESSING_TIME}:${GET_FILES}:${HANDLE_BATCH_EVENT}:${SET_BATCH_OVERRIDES}:${SCALE_CLUSTER}:${START_EXECUTION_MANAGER}:${START_EXECUTION_WORKER}:${DISABLE_PRIVATE_DNS}:${UPDATE_DB}:${UPLOAD_LOG}:${DYNAMO}:${APPS}


build: render
	python -m pip install --upgrade -r requirements-apps-api.txt -t ${API}; \
	python -m pip install --upgrade -r requirements-apps-api-binary.txt --platform manylinux2014_x86_64 --only-binary=:all: -t ${API}; \
	python -m pip install --upgrade -r requirements-apps-handle-batch-event.txt -t ${HANDLE_BATCH_EVENT}; \
	python -m pip install --upgrade -r requirements-apps-scale-cluster.txt -t ${SCALE_CLUSTER}; \
	python -m pip install --upgrade -r requirements-apps-start-execution-manager.txt -t ${START_EXECUTION_MANAGER}; \
	python -m pip install --upgrade -r requirements-apps-start-execution-worker.txt -t ${START_EXECUTION_WORKER}; \
	python -m pip install --upgrade -r requirements-apps-disable-private-dns.txt -t ${DISABLE_PRIVATE_DNS}; \
	python -m pip install --upgrade -r requirements-apps-update-db.txt -t ${UPDATE_DB}

test_file ?= tests/
tests: render
	export $$(xargs < tests/cfg.env); \
	pytest $(test_file)

run: render
	export $$(xargs < tests/cfg.env); \
	python apps/api/src/hyp3_api/__main__.py

install:
	python -m pip install -r requirements-all.txt

files ?= job_spec/*.yml
compute_env_file ?= job_spec/config/compute_environments.yml
security_environment ?= ASF
api_name ?= local
cost_profile ?= DEFAULT
render:
	@echo rendering $(files) for API $(api_name) and security environment $(security_environment); python apps/render_cf.py -j $(files) -e $(compute_env_file) -s $(security_environment) -n $(api_name) -c $(cost_profile)

static: ruff openapi-validate cfn-lint

ruff:
	ruff check . && ruff format --diff .

openapi-validate: render
	openapi-spec-validator apps/api/src/hyp3_api/api-spec/openapi-spec.yml

cfn-lint: render
	cfn-lint --info --ignore-checks W3002 E3008 --template `find . -name *-cf.yml`

clean:
	git ls-files -o -- apps | xargs rm; \
	git ls-files -o -- lib/dynamo | xargs rm; \
	git ls-files -o -- .pytest_cache | xargs rm; \
	find ./ -empty -type d -delete; \
	rm -f packaged.yml

image:
	pwd && docker build --pull -t ${IMAGE_NAME}:latest -f Dockerfile .

shell:
	export AWS_DEFAULT_ACCOUNT=`aws sts get-caller-identity --query 'Account' --output=text --profile ${AWS_PROFILE}` && \
	export AWS_DEFAULT_REGION="${AWS_REGION}" && \
		if [ -z "$$AWS_DEFAULT_ACCOUNT" ]; then echo "⚠️  Can't infer AWS credentials! ⚠️"; fi && \
	docker run --rm -it \
		--entrypoint /bin/bash \
		-v ~/.aws/:/root/.aws/:ro \
		-v ${PWD}:/hyp3/ \
		-e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY \
		-e AWS_DEFAULT_PROFILE -e AWS_PROFILE=${AWS_PROFILE} \
		-e AWS_DEFAULT_REGION -e AWS_REGION=${AWS_REGION} \
		-e AWS_DEFAULT_ACCOUNT \
		-e DEPLOY_PREFIX=${DOCKER_TAG} \
		${IMAGE_NAME}:latest

package:
	@if [ -z "$(ARTIFACT_BUCKET_NAME)" ]; then \
	  echo "Error: ARTIFACT_BUCKET_NAME is not set. Please set it like this: 'make package ARTIFACT_BUCKET_NAME=<your_bucket_name>'"; \
	  exit 1; \
	fi
	@echo "Packaging: ARTIFACT_BUCKET_NAME=$(ARTIFACT_BUCKET_NAME)"

	export AWS_DEFAULT_ACCOUNT=`aws sts get-caller-identity --query 'Account' --output=text --profile ${AWS_PROFILE}` && \
	export AWS_DEFAULT_REGION="${AWS_REGION}" && \
		if [ -z "$$AWS_DEFAULT_ACCOUNT" ]; then echo "⚠️  Can't infer AWS credentials! ⚠️"; fi && \
	docker run --rm -it \
	    --entrypoint /bin/bash \
		-v ~/.aws/:/root/.aws/:ro \
		-v ${PWD}:/hyp3/ \
		-e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY \
		-e AWS_DEFAULT_PROFILE -e AWS_PROFILE=${AWS_PROFILE} \
		-e AWS_DEFAULT_REGION -e AWS_REGION=${AWS_REGION} \
		-e AWS_DEFAULT_ACCOUNT \
		-e DEPLOY_PREFIX=${DOCKER_TAG} \
		${IMAGE_NAME}:latest \
		-c "${PACKAGE_CMD}"
