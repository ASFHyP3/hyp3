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

build: install render
	pip install -r apps/api/requirements-api.txt -t apps/api/src
	pip install -r apps/process-new-granules/requirements-process-new-granules.txt -t apps/process-new-granules/src
	pip install -r apps/update-db/update-db-requirements.txt -t apps/update-db/src
	pip install -r apps/start-execution/start-execution-requirements.txt -t apps/start-execution/src

render:
	@python apps/render_cf.py --job-types-file job_types.yml > /dev/null

static: flake8 openapi-validate

flake8:
	@python -m pip install flake8  flake8-import-order flake8-blind-except flake8-builtins --quiet
	flake8 --max-line-length=120 --import-order-style=pycharm --statistics --application-import-names hyp3_api,get_files,start_execution,update_db,upload_log,dynamo,process_new_granules apps tests lib

openapi-validate: render
	@python -m pip install openapi-spec-validator click prance --quiet
	prance validate --backend=openapi-spec-validator apps/api/src/hyp3_api/api-spec/openapi-spec.yml

