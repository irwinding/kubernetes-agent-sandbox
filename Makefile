.PHONY: install sync run test lint format clean

install:
	uv sync

sync:
	uv sync

run:
	uv run python main.py

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

clean:
	rm -rf .pytest_cache .ruff_cache __pycache__ .venv
	find . -type d -name __pycache__ -exec rm -rf {} +
