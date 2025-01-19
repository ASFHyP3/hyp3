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
ENV_FILE = ${PWD}/env_vars.hyp3.dev

AWS_DEFAULT_PROFILE ?= $(shell grep -E '^AWS_DEFAULT_PROFILE=' $(ENV_FILE) | cut -d '=' -f 2 | sed 's/^$$/default/')
AWS_DEFAULT_REGION ?= $(shell grep -E '^AWS_DEFAULT_REGION=' $(ENV_FILE) | cut -d '=' -f 2 | sed 's/^$$/us-west-2/')
DEPLOY_ENV_IMAGE_NAME ?= hyp3_deploy

SET_AWS_ACCOUNT_ENV_VARS = export AWS_DEFAULT_PROFILE=${AWS_DEFAULT_PROFILE}; \
	export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}; \
	export AWS_DEFAULT_ACCOUNT=`aws sts get-caller-identity --query 'Account' --output=text --profile ${AWS_DEFAULT_PROFILE};`

DOCKER_RUN = docker run --rm -it \
	--entrypoint /bin/bash \
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
	docker build --pull -t ${DEPLOY_ENV_IMAGE_NAME}:latest -f Dockerfile .

shell:
	@{ \
		$(SET_AWS_ACCOUNT_ENV_VARS) && \
        printenv | grep AWS && \
		$(DOCKER_RUN); \
	}

package:
	@{ \
		$(SET_AWS_ACCOUNT_ENV_VARS) && \
        printenv | grep AWS && \
		$(DOCKER_RUN) -c "make install && make build" && \
		$(DOCKER_RUN) -c 'aws cloudformation package \
			--template-file ./apps/main-cf.yml \
			--s3-bucket "$$ARTIFACT_BUCKET_NAME" \
			--output-template-file packaged.yml'; \
	}

deploy:
	@{ \
		$(SET_AWS_ACCOUNT_ENV_VARS) && \
		printenv | grep AWS && \
		$(DOCKER_RUN) -c 'set -e && \
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
		'; \
	}

