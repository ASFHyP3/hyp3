API = ${PWD}/apps/api/src
GET_FILES = ${PWD}/apps/get-files/src
START_EXECUTION = ${PWD}/apps/start-execution/src
UPLOAD_LOG = ${PWD}/apps/upload-log/src
PROCESS_NEW_GRANULES = ${PWD}/apps/process-new-granules/src
DYNAMO = ${PWD}/lib/dynamo
export PYTHONPATH = ${API}:${GET_FILES}:${START_EXECUTION}:${UPLOAD_LOG}:${PROCESS_NEW_GRANULES}:${DYNAMO}

tests: install render
	export $$(xargs < tests/cfg.env); \
	pytest tests/test_api

run: install render
	export $$(xargs < tests/cfg.env); \
	python apps/api/src/hyp3_api/__main__.py

install:
	python -m pip install -r requirements-all.txt

render:
	python apps/render_cf.py --job-types-file job_types.yml
