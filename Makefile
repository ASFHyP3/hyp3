SHELL := /bin/bash

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
AWS_DEFAULT_PROFILE ?= default
AWS_REGION ?= us-west-2
DOCKER_TAG ?= test
IMAGE_NAME ?= hyp3_deploy
DEFAULT_APP_STATUS ?= NOT_STARTED
DEFAULT_CREDITS_PER_USER ?= 1000

AWS_ACCOUNT_CMD = export AWS_DEFAULT_ACCOUNT=`aws sts get-caller-identity --query 'Account' --output=text --profile ${AWS_DEFAULT_PROFILE}`
AWS_REGION_CMD = export AWS_DEFAULT_REGION="${AWS_REGION}"

CHECK_AWS_CREDENTIALS = if [ -z "$$AWS_DEFAULT_ACCOUNT" ]; then echo "⚠️  Can't infer AWS credentials! ⚠️"; fi

DOCKER_RUN = docker run --rm -it \
	--entrypoint /bin/bash \
	-v ~/.aws/:/root/.aws/:ro \
	-v /tmp/aws-cli-cache:/root/.aws/cli/cache \
	-v ${PWD}:/hyp3/ \
	-e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY \
	-e AWS_DEFAULT_PROFILE \
	-e AWS_DEFAULT_REGION \
	-e AWS_DEFAULT_ACCOUNT \
	-e DEPLOY_PREFIX=${DOCKER_TAG} \
	${IMAGE_NAME}:latest

PACKAGE_CMD = aws cloudformation package \
		--template-file ./apps/main-cf.yml \
		--s3-bucket $(ARTIFACT_BUCKET_NAME) \
		--output-template-file packaged.yml \

DEPLOY_CMD = aws cloudformation deploy \
		--stack-name ${STACK_NAME} \
		--template-file ./packaged.yml \
		--capabilities CAPABILITY_IAM \
		--parameter-overrides \
			"VpcId=${VPC_ID}" \
			"SubnetIds=${SUBNET_IDS}" \
			"DomainName=${CUSTOM_API_DOMAIN}" \
			"CertificateArn=${SSH_CERT_ARN}" \
			"DefaultApplicationStatus=${DEFAULT_APP_STATUS}" \
			"SecretArn=${EDL_SECRET_ARN}" \
			\"AuthPublicKey=${AUTH_PUBLIC_KEY}\" \
		"DefaultCreditsPerUser=${DEFAULT_CREDITS_PER_USER}" \


define REQUIRE_ARG
	@if [ -z "$($(1))" ]; then \
	  echo "Error: $(1) is not set. Please set it like this: 'make $(2) $(1)=<value>'"; \
	  exit 1; \
	fi
endef

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
	@$(AWS_ACCOUNT_CMD) && \
	$(AWS_REGION_CMD) && \
	$(CHECK_AWS_CREDENTIALS) && \
	$(DOCKER_RUN)

run-docker-cmd:
	@$(AWS_ACCOUNT_CMD) && \
	$(AWS_REGION_CMD) && \
	$(CHECK_AWS_CREDENTIALS) && \
	$(DOCKER_RUN) -c "$(CMD)"

package:
	$(call REQUIRE_ARG,ARTIFACT_BUCKET_NAME,package)
	@echo "Packaging: ARTIFACT_BUCKET_NAME=$(ARTIFACT_BUCKET_NAME)"
	$(MAKE) run-docker-cmd CMD="make install && make build" && \
	$(MAKE) run-docker-cmd CMD="$(PACKAGE_CMD)"

deploy:
	$(call REQUIRE_ARG,STACK_NAME,deploy)
	$(call REQUIRE_ARG,VPC_ID,deploy)
	$(call REQUIRE_ARG,SUBNET_IDS,deploy)
	$(call REQUIRE_ARG,CUSTOM_API_DOMAIN,deploy)
	$(call REQUIRE_ARG,SSH_CERT_ARN,deploy)
	$(call REQUIRE_ARG,EDL_SECRET_ARN,deploy)
	$(call REQUIRE_ARG,AUTH_PUBLIC_KEY,deploy)


	@echo "$(DEPLOY_CMD)"

	$(MAKE) run-docker-cmd CMD="$(DEPLOY_CMD)"
