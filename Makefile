API = ${PWD}/apps/api/src
GET_FILES = ${PWD}/apps/get-files/src
PROCESS_NEW_GRANULES = ${PWD}/apps/process-new-granules/src
SCALE_CLUSTER = ${PWD}/apps/scale-cluster/src
START_EXECUTION = ${PWD}/apps/start-execution/src
UPDATE_DB = ${PWD}/apps/update-db/src
UPLOAD_LOG = ${PWD}/apps/upload-log/src
DYNAMO = ${PWD}/lib/dynamo
export PYTHONPATH = ${API}:${GET_FILES}:${PROCESS_NEW_GRANULES}:${SCALE_CLUSTER}:${START_EXECUTION}:${UPDATE_DB}:${UPLOAD_LOG}:${DYNAMO}


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
render:
	@echo rendering $(files); python apps/render_cf.py $(files)

static: flake8 openapi-validate cfn-lint

flake8:
	flake8 --max-line-length=120 --import-order-style=pycharm --statistics --application-import-names hyp3_api,get_files,start_execution,update_db,upload_log,dynamo,process_new_granules,scale_cluster apps tests lib

openapi-validate: render
	prance validate --backend=openapi-spec-validator apps/api/src/hyp3_api/api-spec/openapi-spec.yml

cfn-lint: render
	cfn-lint --info --ignore-checks W3002 --template `find . -name *-cf.yml`

clean:
	rm -f apps/api/src/hyp3_api/api-spec/job_parameters.yml \
	    apps/api/src/hyp3_api/job_validation_map.yml \
	    apps/step-function.json \
	    apps/workflow-cf.yml

distclean: clean
	git ls-files -o -- apps | xargs rm; \
	find ./apps/ -empty -type d -delete; \
	rm -f packaged.yml
