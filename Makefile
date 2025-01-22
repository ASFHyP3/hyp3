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
ENV_FILE = ${PWD}/hyp3.env

DEFAULT_PROFILE := default
EXTRACTED_PROFILE := $(shell grep -E '^AWS_DEFAULT_PROFILE=' $(ENV_FILE) | cut -d '=' -f 2 | sed 's/^$$/${DEFAULT_PROFILE}/')
AWS_DEFAULT_PROFILE ?= $(shell [ -z "$(EXTRACTED_PROFILE)" ] && echo "$(DEFAULT_PROFILE)" || echo "$(EXTRACTED_PROFILE)")

DEFAULT_REGION := us-west-2
EXTRACTED_REGION := $(shell grep -E '^AWS_DEFAULT_REGION=' $(ENV_FILE) | cut -d '=' -f 2 | sed 's/^$$/$(DEFAULT_REGION)/')
AWS_DEFAULT_REGION ?= $(shell [ -z "$(EXTRACTED_REGION)" ] && echo "$(DEFAULT_REGION)" || echo "$(EXTRACTED_REGION)")

DEPLOY_ENV_IMAGE_NAME ?= hyp3_deploy

SET_AWS_ACCOUNT_ENV_VARS = export AWS_DEFAULT_PROFILE=${AWS_DEFAULT_PROFILE}; \
	export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}; \
	export AWS_DEFAULT_ACCOUNT=`aws sts get-caller-identity --query 'Account' --output=text --profile ${AWS_DEFAULT_PROFILE};`

DOCKER_RUN = docker run --rm -it \
	--env-file $(ENV_FILE) \
	-v ~/.aws/:/root/.aws/:ro \
	-v /tmp/aws-cli-cache:/root/.aws/cli/cache \
	-v ${PWD}:/hyp3/ \
	-e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY \
	-e AWS_DEFAULT_PROFILE \
	-e AWS_DEFAULT_REGION \
	-e AWS_DEFAULT_ACCOUNT \
	${DEPLOY_ENV_IMAGE_NAME}:latest

PACKAGE_CMD = aws cloudformation package \
		--template-file ./apps/main-cf.yml \
		--s3-bucket \$$ARTIFACT_BUCKET_NAME \
		--output-template-file packaged.yml \

DEPLOY_CMD = aws cloudformation deploy \
		--stack-name \$$STACK_NAME \
		--template-file ./packaged.yml \
		--capabilities CAPABILITY_IAM \
		--parameter-overrides \
			"VpcId=\$$VPC_ID" \
			"SubnetIds=\$$SUBNET_IDS" \
			"DomainName=\$$DOMAIN_NAME" \
			"CertificateArn=\$$CERT_ARN" \
			"DefaultApplicationStatus=\$$DEFAULT_APP_STATUS" \
			"SecretArn=\$$EDL_SECRET_ARN" \
			"AuthPublicKey=\$$AUTH_PUBLIC_KEY" \
			"DefaultCreditsPerUser=\$$DEFAULT_CREDITS_PER_USER" \

export PYTHONPATH = ${API}:${CHECK_PROCESSING_TIME}:${GET_FILES}:${HANDLE_BATCH_EVENT}:${SET_BATCH_OVERRIDES}:${SCALE_CLUSTER}:${START_EXECUTION_MANAGER}:${START_EXECUTION_WORKER}:${DISABLE_PRIVATE_DNS}:${UPDATE_DB}:${UPLOAD_LOG}:${DYNAMO}:${APPS}


.PHONY: help
help: ## Show this help message
	@echo "Available targets:"
	@awk -F ':.*##' '/^[a-zA-Z0-9_-]+:.*##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST) | sort
	@echo -e "\n\nTo deploy HyP3:\n" \
	     "  1. Complete prerequisite steps listed in README.md\n" \
	     "  2. Create a 'hyp3.env' file based on 'hyp3.example'\n" \
		 "  3. Run the following make targets in order:\n" \
	     "    a. make image\n" \
	     "    b. make package\n" \
	     "    c. make deploy"

.PHONY: build
build: render ## Build HyP3
	python -m pip install --upgrade -r requirements-apps-api.txt -t ${API}; \
	python -m pip install --upgrade -r requirements-apps-api-binary.txt --platform manylinux2014_x86_64 --only-binary=:all: -t ${API}; \
	python -m pip install --upgrade -r requirements-apps-handle-batch-event.txt -t ${HANDLE_BATCH_EVENT}; \
	python -m pip install --upgrade -r requirements-apps-scale-cluster.txt -t ${SCALE_CLUSTER}; \
	python -m pip install --upgrade -r requirements-apps-start-execution-manager.txt -t ${START_EXECUTION_MANAGER}; \
	python -m pip install --upgrade -r requirements-apps-start-execution-worker.txt -t ${START_EXECUTION_WORKER}; \
	python -m pip install --upgrade -r requirements-apps-disable-private-dns.txt -t ${DISABLE_PRIVATE_DNS}; \
	python -m pip install --upgrade -r requirements-apps-update-db.txt -t ${UPDATE_DB}

test_file ?= tests/
.PHONY: tests
tests: render ## Run HyP3 tests
	export $$(xargs < tests/cfg.env); \
	pytest $(test_file)

.PHONY: run
run: render ## Run the HyP3 API locally on port 8080
	export $$(xargs < tests/cfg.env); \
	python apps/api/src/hyp3_api/__main__.py

.PHONY: install
install: ## Installs required Python software with pip
	python -m pip install -r requirements-all.txt

files ?= job_spec/*.yml
compute_env_file ?= job_spec/config/compute_environments.yml
security_environment ?= ASF
api_name ?= local
cost_profile ?= DEFAULT
.PHONY: render
render: ## Render CloudFormation templates using HyP3 job specs and environment configs
	@echo rendering $(files) for API $(api_name) and security environment $(security_environment); python apps/render_cf.py -j $(files) -e $(compute_env_file) -s $(security_environment) -n $(api_name) -c $(cost_profile)

.PHONY: static
static: ## Perform static analysis with openapi-validate and ruff
	ruff openapi-validate cfn-lint

.PHONY: ruff
ruff: ## Lint and format Python code with ruff
	ruff check . && ruff format --diff .

.PHONY: openapi-validate
openapi-validate: render ## Validate openapi spec
	openapi-spec-validator apps/api/src/hyp3_api/api-spec/openapi-spec.yml

.PHONY: render cfn-lint
cfn-lint: ## Lint CloudFormation templates
	cfn-lint --info --ignore-checks W3002 E3008 --template `find . -name *-cf.yml`

.PHONY: clean
clean: ## Remove local build files
	@{ \
		if [ -f /.dockerenv ]; then \
			echo \'make clean\' will remove your HyP3 deployment container; \
		    echo Run \'make clean\' outside of you HyP3 deployment container; \
		else \
			git ls-files -o -- apps | xargs rm; \
			git ls-files -o -- lib/dynamo | xargs rm; \
			git ls-files -o -- .pytest_cache | xargs rm; \
			find ./ -empty -type d -delete; \
			rm -f packaged.yml; \
			if command -v docker >/dev/null 2>&1; then \
				if docker info >/dev/null 2>&1; then \
					docker rmi -f ${DEPLOY_ENV_IMAGE_NAME}:latest 2>/dev/null || true; \
				else \
					echo "Docker is installed but the Docker engine is not running. Skipping deployment image cleanup."; \
				fi; \
			fi; \
		fi; \
	}

.PHONY: image
image: ## Create a containerized HyP3 deployment environment
	docker build --pull -t ${DEPLOY_ENV_IMAGE_NAME}:latest -f Dockerfile .

.PHONY: shell
shell: ## Run a shell on Hyp3 deployment container (created with 'make image')
	@{ \
		$(SET_AWS_ACCOUNT_ENV_VARS) && \
        printenv | grep AWS && \
		$(DOCKER_RUN); \
	}

.PHONY: package
package: ## Run 'make install && make build', and package CloudFormation artifacts
	aws cloudformation package \
		--template-file ./apps/main-cf.yml \
		--s3-bucket "$$ARTIFACT_BUCKET_NAME" \
		--output-template-file packaged.yml; \


.PHONY: deploy
deploy: ## Deploy HyP3 with AWS CloudFormation
	@{ \
		set -e && \
		PARAM_OVERRIDES="" && \
		declare -A PARAMS=( \
			[AMI_ID]="AmiId" \
			[AUTH_ALGORITHM]="AuthAlgorithm" \
			[AUTH_PUBLIC_KEY]="AuthPublicKey" \
			[CERT_ARN]="CertificateArn" \
			[DEFAULT_APP_STATUS]="DefaultApplicationStatus" \
			[DEFAULT_CREDITS_PER_USER]="DefaultCreditsPerUser" \
			[DEFAULT_MAX_VCPUS]="DefaultMaxvCpus" \
			[DOMAIN_NAME]="DomainName" \
			[EXPANDED_MAX_VCPUS]="ExpandedMaxvCpus" \
			[IMAGE_TAG]="ImageTag" \
			[INSTANCE_TYPES]="InstanceTypes" \
			[MONTHLY_BUDGET]="MonthlyBudget" \
			[PRODUCT_LIFETIME_IN_DAYS]="ProductLifetimeInDays" \
			[REQUIRED_SURPLUS]="RequiredSurplus" \
			[SECRET_ARN]="SecretArn" \
			[SUBNET_IDS]="SubnetIds" \
			[SYSTEM_AVAILABLE]="SystemAvailable" \
			[VPC_ID]="VpcId" \
		); \
		for var in "$${!PARAMS[@]}"; do \
			value="$${!var}"; \
			[ -n "$$value" ] && PARAM_OVERRIDES="$$PARAM_OVERRIDES $${PARAMS[$$var]}=$$value"; \
		done; \
		aws cloudformation deploy \
			--stack-name "$$STACK_NAME" \
			--template-file ./packaged.yml \
			--capabilities CAPABILITY_IAM \
			--parameter-overrides "$$PARAM_OVERRIDES"; \
	}

