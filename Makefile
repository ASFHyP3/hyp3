API = ${PWD}/apps/api/src
CHECK_PROCESSING_TIME = ${PWD}/apps/check-processing-time/src
GET_FILES = ${PWD}/apps/get-files/src
PROCESS_NEW_GRANULES = ${PWD}/apps/process-new-granules/src
SCALE_CLUSTER = ${PWD}/apps/scale-cluster/src
START_EXECUTION = ${PWD}/apps/start-execution/src
UPDATE_DB = ${PWD}/apps/update-db/src
UPLOAD_LOG = ${PWD}/apps/upload-log/src
DYNAMO = ${PWD}/lib/dynamo
export PYTHONPATH = ${API}:${CHECK_PROCESSING_TIME}:${GET_FILES}:${PROCESS_NEW_GRANULES}:${SCALE_CLUSTER}:${START_EXECUTION}:${UPDATE_DB}:${UPLOAD_LOG}:${DYNAMO}


build: render
	python -m pip install --upgrade -r requirements-apps-api.txt -t ${API}; \
	python -m pip install --upgrade -r requirements-apps-process-new-granules.txt -t ${PROCESS_NEW_GRANULES}; \
	python -m pip install --upgrade -r requirements-apps-scale-cluster.txt -t ${SCALE_CLUSTER}; \
	python -m pip install --upgrade -r requirements-apps-start-execution.txt -t ${START_EXECUTION}; \
	python -m pip install --upgrade -r requirements-apps-update-db.txt -t ${UPDATE_DB}

tests: render
	export $$(xargs < tests/cfg.env); \
	pytest tests

run: render
	export $$(xargs < tests/cfg.env); \
	python apps/api/src/hyp3_api/__main__.py

install:
	python -m pip install -r requirements-all.txt

files ?= job_spec/*.yml
security_environment ?= ASF
instance_sizes ?= rd5.xlarge
render:
	@echo rendering $(files) for $(security_environment); python apps/render_cf.py -j $(files) -s $(security_environment) -i $(instance_sizes)

static: flake8 openapi-validate cfn-lint

flake8:
	flake8 --max-line-length=120 --import-order-style=pycharm --statistics --application-import-names hyp3_api,get_files,check_processing_time,start_execution,update_db,upload_log,dynamo,process_new_granules,scale_cluster apps tests lib

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
