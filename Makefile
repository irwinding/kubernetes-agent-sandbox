.PHONY: install sync run test unit integration integration-local lint format clean

install:
	uv sync

sync:
	uv sync

run:
	uv run python main.py

test:
	uv run python -m pytest

unit:
	uv run python -m pytest tests/unit_tests

integration:
	uv run python -m pytest tests/integration_tests

# Run integration tests against your current kubectl context.
# Requires a local cluster with the agent-sandbox operator installed.
# Override on the command line, e.g.:
#   make integration-local K8S_SANDBOX_TEMPLATE=python
K8S_SANDBOX_TEMPLATE ?= default
K8S_SANDBOX_NAMESPACE ?= default
integration-local:
	K8S_LOCAL_INTEGRATION=1 \
	K8S_SANDBOX_TEMPLATE=$(K8S_SANDBOX_TEMPLATE) \
	K8S_SANDBOX_NAMESPACE=$(K8S_SANDBOX_NAMESPACE) \
	uv run python -m pytest tests/integration_tests -v

lint:
	uv run ruff check .

format:
	uv run ruff format .

clean:
	rm -rf .pytest_cache .ruff_cache __pycache__ .venv
	find . -type d -name __pycache__ -exec rm -rf {} +
