API = ${PWD}/apps/api/src
APPS = ${PWD}/apps
CHECK_PROCESSING_TIME = ${PWD}/apps/check-processing-time/src
GET_FILES = ${PWD}/apps/get-files/src
HANDLE_BATCH_EVENT = ${PWD}/apps/handle-batch-event/src
SET_BATCH_OVERRIDES = ${PWD}/apps/set-batch-overrides/src
SCALE_CLUSTER = ${PWD}/apps/scale-cluster/src
START_EXECUTION = ${PWD}/apps/start-execution/src
DISABLE_PRIVATE_DNS = ${PWD}/apps/disable-private-dns/src
UPDATE_DB = ${PWD}/apps/update-db/src
UPLOAD_LOG = ${PWD}/apps/upload-log/src
DYNAMO = ${PWD}/lib/dynamo
LAMBDA_LOGGING = ${PWD}/lib/lambda_logging
export PYTHONPATH = ${API}:${CHECK_PROCESSING_TIME}:${GET_FILES}:${HANDLE_BATCH_EVENT}:${SET_BATCH_OVERRIDES}:${SCALE_CLUSTER}:${START_EXECUTION}:${DISABLE_PRIVATE_DNS}:${UPDATE_DB}:${UPLOAD_LOG}:${DYNAMO}:${LAMBDA_LOGGING}:${APPS}


build: render
	python -m pip install --upgrade -r requirements-apps-api.txt -t ${API}; \
	python -m pip install --upgrade -r requirements-apps-api-binary.txt --platform manylinux2014_x86_64 --only-binary=:all: -t ${API}; \
	python -m pip install --upgrade -r requirements-apps-handle-batch-event.txt -t ${HANDLE_BATCH_EVENT}; \
	python -m pip install --upgrade -r requirements-apps-scale-cluster.txt -t ${SCALE_CLUSTER}; \
	python -m pip install --upgrade -r requirements-apps-start-execution.txt -t ${START_EXECUTION}; \
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
