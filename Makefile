PY ?= python3
export PYTHONPATH := src

.PHONY: demo validate test test-perf lint type gen-synthetic bench docker helm-lint

demo:          ## reference-implementation smoke demo
	$(PY) scripts/demo_reference.py

validate:      ## validate the default configuration
	$(PY) -m streamsieve.cli.main validate-config --config configs/default.yaml

test:          ## unit + integration tests
	$(PY) -m pytest tests/unit tests/integration -q

test-perf:     ## performance regression (latency-budget gate)
	$(PY) -m pytest tests/perf -q -m perf

lint:          ## static checks
	$(PY) -m ruff check src scripts tests

type:          ## type checking
	$(PY) -m mypy src/streamsieve

gen-synthetic: ## generate synthetic test streams
	$(PY) scripts/gen_synthetic_stream.py --out var/synthetic --frames 300

bench:         ## matched-baseline benchmark (module bodies required first)
	$(PY) -m streamsieve.cli.main bench --config configs/profiles/cloud_t4.yaml

docker:        ## build the CPU image
	docker build -f deployments/docker/Dockerfile.cpu -t streamsieve:cpu .

helm-lint:
	helm lint deployments/helm/streamsieve
