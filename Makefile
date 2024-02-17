API = ${PWD}/apps/api/src
CHECK_PROCESSING_TIME = ${PWD}/apps/check-processing-time/src
GET_FILES = ${PWD}/apps/get-files/src
HANDLE_BATCH_EVENT = ${PWD}/apps/handle-batch-event/src
SCALE_CLUSTER = ${PWD}/apps/scale-cluster/src
START_EXECUTION_MANAGER = ${PWD}/apps/start-execution-manager/src
START_EXECUTION_WORKER = ${PWD}/apps/start-execution-worker/src
DISABLE_PRIVATE_DNS = ${PWD}/apps/disable-private-dns/src
UPDATE_DB = ${PWD}/apps/update-db/src
UPLOAD_LOG = ${PWD}/apps/upload-log/src
DYNAMO = ${PWD}/lib/dynamo
export PYTHONPATH = ${API}:${CHECK_PROCESSING_TIME}:${GET_FILES}:${HANDLE_BATCH_EVENT}:${SCALE_CLUSTER}:${START_EXECUTION_MANAGER}:${START_EXECUTION_WORKER}:${DISABLE_PRIVATE_DNS}:${UPDATE_DB}:${UPLOAD_LOG}:${DYNAMO}


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
security_environment ?= ASF
api_name ?= local
cost_profile ?= None
render:
	@echo rendering $(files) for API $(api_name) and security environment $(security_environment); python apps/render_cf.py -j $(files) -s $(security_environment) -n $(api_name) -c $(cost_profile)

static: flake8 openapi-validate cfn-lint

flake8:
	flake8 --ignore=E731 --max-line-length=120 --import-order-style=pycharm --statistics --application-import-names hyp3_api,get_files,handle_batch_event,check_processing_time,start_execution_manager,start_execution_worker,disable_private_dns,update_db,upload_log,dynamo,lambda_logging,scale_cluster apps tests lib

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
