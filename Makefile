API = ${PWD}/apps/api/src
GET_FILES = ${PWD}/apps/get-files/src
START_EXECUTION = ${PWD}/apps/start-execution/src
UPLOAD_LOG = ${PWD}/apps/upload-log/src
PROCESS_NEW_GRANULES = ${PWD}/apps/process-new-granules/src
DYNAMO = ${PWD}/lib/dynamo
export PYTHONPATH = ${API}:${GET_FILES}:${START_EXECUTION}:${UPLOAD_LOG}:${PROCESS_NEW_GRANULES}:${DYNAMO}

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
	@echo $(files); python apps/render_cf.py $(files)

static: flake8 openapi-validate cfn-lint

flake8:
	@python -m pip install flake8  flake8-import-order flake8-blind-except flake8-builtins --quiet
	flake8 --max-line-length=120 --import-order-style=pycharm --statistics --application-import-names hyp3_api,get_files,start_execution,update_db,upload_log,dynamo,process_new_granules apps tests lib

openapi-validate: render
	@python -m pip install openapi-spec-validator click prance --quiet
	prance validate --backend=openapi-spec-validator apps/api/src/hyp3_api/api-spec/openapi-spec.yml

cfn-lint: render
	@python -m pip install cfn-lint --quiet
	cfn-lint --info --ignore-checks W3002 --template **/*cf.yml

clean:
	rm -f apps/api/src/hyp3_api/api-spec/job_parameters.yml \
	    apps/api/src/hyp3_api/job_validation_map.yml \
	    apps/step-function.json \
	    apps/workflow-cf.yml
