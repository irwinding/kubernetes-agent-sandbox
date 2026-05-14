.PHONY: test unit integration coverage clean

test:
	uv run python -m pytest

unit:
	uv run python -m pytest unit_tests

integration:
	uv run python -m pytest integration_tests

coverage:
	uv run python -m pytest --cov=langchain_kubernetes_agent_sandbox --cov-report=term-missing

clean:
	rm -rf .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
