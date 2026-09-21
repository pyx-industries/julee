# Makefile for quality checks, testing and docs
# Requires uv: https://docs.astral.sh/uv/getting-started/installation/
.PHONY: install check docs lint-python typecheck test-python-unit test-doctrine quality-fast-python quality-full quality-types quality-security test-unit post-commit install-hooks reports clean help format-python update-requirements

# Install project and dev dependencies
install:
	uv sync --extra dev

# Python linting
lint-python:
	@echo "Linting Python code..."
	uv run black --check src/julee/
	uv run ruff check src/julee/

# Type checking (fails on errors)
typecheck:
	@echo "Type checking..."
	uv run mypy src/julee/

# Python unit tests
test-python-unit:
	@echo "Running Python unit tests..."
	uv run pytest -m unit

# Doctrine tests against julee itself
test-doctrine:
	@echo "Running doctrine tests..."
	uv run pytest src/julee/core/doctrine/

# The checks CI runs; run before pushing
check: lint-python typecheck test-python-unit test-doctrine

# Build the documentation
docs:
	uv run --extra docs sphinx-build -b html docs docs/_build/html

# Fast Python quality checks (for pre-commit)
quality-fast-python: lint-python
	uv run pytest --asyncio-mode=auto -x -m unit --no-cov -q

# Full quality suite (for post-commit/CI)
quality-full: reports quality-types quality-security test-unit
	@echo "All quality checks complete!"

# Type checking
quality-types: reports
	@echo "Type checking..."
	uv run mypy src/julee/ > reports/mypy.txt 2>&1 || true

# Security scanning
quality-security: reports
	@echo "Security scanning..."
	uv run bandit -r src/julee --severity-level=high -f json -o reports/bandit-high.json 2>/dev/null || true
	uv run bandit -r src/julee --severity-level=medium -f json -o reports/bandit-medium-high.json 2>/dev/null || true
	uv run bandit -r src/julee --severity-level=low -f json -o reports/bandit-all.json 2>/dev/null || true
	uv run bandit -r src/julee --severity-level=high -f txt -o reports/bandit-high.txt 2>/dev/null || true
	@echo "Security scan complete:"
	@echo "  - High severity only: reports/bandit-high.json, reports/bandit-high.txt"
	@echo "  - Medium+High severity: reports/bandit-medium-high.json"
	@echo "  - All severities: reports/bandit-all.json"

# Unit tests with coverage
test-unit: reports
	@echo "Running unit tests with coverage..."
	uv run pytest --asyncio-mode=auto --cov=src/julee --cov-fail-under=60 --cov-report=html:reports/htmlcov --cov-report=xml:reports/coverage.xml -m "not e2e"

# Setup reports directory
reports:
	@mkdir -p reports

# Post-commit hook (run in background)
post-commit: reports
	@echo "Running post-commit quality suite in background..."
	@nohup make quality-full > reports/post-commit.log 2>&1 &
	@echo "Quality checks running in background. Check reports/ for results."

# Install project-specific git hooks
install-hooks:
	@echo "#!/bin/bash" > .git/hooks/post-commit
	@echo "make post-commit" >> .git/hooks/post-commit
	@chmod +x .git/hooks/post-commit
	@echo "Post-commit hook installed for this repository only"

# Clean up generated files
clean:
	@echo "Cleaning up..."
	rm -rf reports/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf **/__pycache__/
	rm -rf **/*.pyc
	@echo "Cleanup complete"

# Format Python code
format-python:
	@echo "Formatting Python code..."
	uv run black src/julee/
	uv run ruff check --fix src/julee/

# Update uv.lock from pyproject.toml
update-requirements:
	@echo "Updating uv.lock from pyproject.toml..."
	uv lock --upgrade
	@echo "Lock file updated! Review changes before committing."

# Help target
help:
	@echo "Available targets:"
	@echo "  check           - The checks CI runs (lint, types, unit, doctrine)"
	@echo "  docs            - Build the documentation"
	@echo "  test-doctrine   - Doctrine tests against julee itself"
	@echo "  lint-python     - Python linting (black, ruff)"
	@echo "  test-python-unit - Python unit tests"
	@echo "  quality-fast-python - Fast Python quality checks (lint + unit tests)"
	@echo "  quality-full    - Full quality suite (types, security, all tests)"
	@echo "  quality-types   - Type checking with mypy"
	@echo "  quality-security- Security scanning with bandit"
	@echo "  test-unit       - Unit tests with coverage"
	@echo "  post-commit     - Background quality checks (for git hook)"
	@echo "  install-hooks   - Install git post-commit hook"
	@echo "  install         - Install project and dev dependencies via uv"
	@echo "  format-python   - Format Python code with black and ruff"
	@echo "  update-requirements - Upgrade uv.lock from pyproject.toml"
	@echo "  clean           - Clean up generated files"
	@echo "  reports         - Create reports directory"
	@echo "  help            - Show this help"
