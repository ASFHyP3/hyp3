API = ${PWD}/apps/api/src
CHECK_PROCESSING_TIME = ${PWD}/apps/check-processing-time/src
GET_FILES = ${PWD}/apps/get-files/src
HANDLE_BATCH_EVENT = ${PWD}/apps/handle-batch-event/src
PROCESS_NEW_GRANULES = ${PWD}/apps/process-new-granules/src
SCALE_CLUSTER = ${PWD}/apps/scale-cluster/src
START_EXECUTION = ${PWD}/apps/start-execution/src
UPDATE_DB = ${PWD}/apps/update-db/src
UPLOAD_LOG = ${PWD}/apps/upload-log/src
DYNAMO = ${PWD}/lib/dynamo
export PYTHONPATH = ${API}:${CHECK_PROCESSING_TIME}:${GET_FILES}:${HANDLE_BATCH_EVENT}:${PROCESS_NEW_GRANULES}:${SCALE_CLUSTER}:${START_EXECUTION}:${UPDATE_DB}:${UPLOAD_LOG}:${DYNAMO}


build: render
	python -m pip install --platform manylinux2014_x86_64 --only-binary=:all: --upgrade -r requirements-apps-api.txt -t ${API}; \
	python -m pip install --platform manylinux2014_x86_64 --only-binary=:all: --upgrade -r requirements-apps-handle-batch-event.txt -t ${HANDLE_BATCH_EVENT}; \
	python -m pip install --platform manylinux2014_x86_64 --only-binary=:all: --upgrade -r requirements-apps-process-new-granules.txt -t ${PROCESS_NEW_GRANULES}; \
	python -m pip install --platform manylinux2014_x86_64 --only-binary=:all: --upgrade -r requirements-apps-scale-cluster.txt -t ${SCALE_CLUSTER}; \
	python -m pip install --platform manylinux2014_x86_64 --only-binary=:all: --upgrade -r requirements-apps-start-execution.txt -t ${START_EXECUTION}; \
	python -m pip install --platform manylinux2014_x86_64 --only-binary=:all: --upgrade -r requirements-apps-update-db.txt -t ${UPDATE_DB}

tests: render
	export $$(xargs < tests/cfg.env); \
	pytest tests

run: render
	export $$(xargs < tests/cfg.env); \
	python apps/api/src/hyp3_api/__main__.py

install:
	python -m pip install --platform manylinux2014_x86_64 --only-binary=:all: -r requirements-all.txt

files ?= job_spec/*.yml
security_environment ?= ASF
api_name ?= local
render:
	@echo rendering $(files) for API $(api_name) and security environment $(security_environment); python apps/render_cf.py -j $(files) -s $(security_environment) -n $(api_name)

static: flake8 openapi-validate cfn-lint

flake8:
	flake8 --ignore=E731 --max-line-length=120 --import-order-style=pycharm --statistics --application-import-names hyp3_api,get_files,handle_batch_event,check_processing_time,start_execution,update_db,upload_log,dynamo,process_new_granules,scale_cluster apps tests lib

openapi-validate: render
	prance validate --backend=openapi-spec-validator apps/api/src/hyp3_api/api-spec/openapi-spec.yml

cfn-lint: render
	cfn-lint --info --ignore-checks W3002 E3008 --template `find . -name *-cf.yml`

clean:
	git ls-files -o -- apps | xargs rm; \
	git ls-files -o -- lib/dynamo | xargs rm; \
	git ls-files -o -- .pytest_cache | xargs rm; \
	find ./ -empty -type d -delete; \
	rm -f packaged.yml
