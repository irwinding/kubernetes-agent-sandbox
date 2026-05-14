.PHONY: test unit integration integration-local coverage clean

test:
	uv run python -m pytest

unit:
	uv run python -m pytest unit_tests

integration:
	uv run python -m pytest integration_tests

# Runs integration tests against your current kubectl context.
# Requires a local cluster with the agent-sandbox operator installed.
# Override K8S_SANDBOX_TEMPLATE / K8S_SANDBOX_NAMESPACE on the command line:
#   make integration-local K8S_SANDBOX_TEMPLATE=python
K8S_SANDBOX_TEMPLATE ?= default
K8S_SANDBOX_NAMESPACE ?= default
integration-local:
	K8S_LOCAL_INTEGRATION=1 \
	K8S_SANDBOX_TEMPLATE=$(K8S_SANDBOX_TEMPLATE) \
	K8S_SANDBOX_NAMESPACE=$(K8S_SANDBOX_NAMESPACE) \
	uv run python -m pytest integration_tests -v

coverage:
	uv run python -m pytest --cov=langchain_kubernetes_agent_sandbox --cov-report=term-missing

clean:
	rm -rf .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
