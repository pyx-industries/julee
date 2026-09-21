# Makefile for quality checks, testing and docs
# Requires uv: https://docs.astral.sh/uv/getting-started/installation/
.PHONY: install check docs lint-python typecheck test-python-unit test-integration test-doctrine test-doctrine-kits quality-fast-python quality-full quality-types quality-security test-unit reports clean help format-python update-requirements

# Install project and dev dependencies
install:
	uv sync --extra dev

# Python linting
lint-python:
	@echo "Linting Python code..."
	uv run black --check src/julee/ viewpoints/src/
	uv run ruff check src/julee/ viewpoints/src/

# Type checking (fails on errors)
typecheck:
	@echo "Type checking..."
	uv run mypy src/julee/ viewpoints/src/

# Python unit tests: every test that needs nothing but Python. They are
# chosen by what is left out, not by -m unit, so that a test with no marker
# runs rather than hides. Doctrine has its own targets below.
test-python-unit:
	@echo "Running Python unit tests..."
	uv run pytest -m "not integration and not e2e and not llm and not contract" --ignore=src/julee/core/doctrine

# Doctrine tests against julee itself
test-doctrine:
	@echo "Running doctrine tests..."
	uv run pytest src/julee/core/doctrine/

# Doctrine tests against each kit in this workspace
test-doctrine-kits:
	@echo "Running doctrine tests for julee-viewpoints..."
	JULEE_TARGET=viewpoints uv run pytest src/julee/core/doctrine/

# The checks CI runs; run before pushing
check: lint-python typecheck test-python-unit test-integration test-doctrine test-doctrine-kits

# Build the documentation
docs:
	uv run --extra docs sphinx-build -W --keep-going -b html docs docs/_build/html

# Fast Python quality checks (for pre-commit)
quality-fast-python: lint-python
	uv run pytest --asyncio-mode=auto -x -m unit --no-cov -q

# Full quality suite, slower than check: types, security scan, coverage
quality-full: reports quality-types quality-security test-unit
	@echo "All quality checks complete!"

# Type checking
quality-types: reports
	@echo "Type checking..."
	uv run mypy src/julee/ viewpoints/src/ > reports/mypy.txt 2>&1 || true

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

# Unit tests with coverage. Integration tests are excluded: they each
# start a Temporal test server, and a suite that needs a server is not
# what a caller of this target is asking for.
test-unit: reports
	@echo "Running unit tests with coverage..."
	uv run pytest --asyncio-mode=auto --cov=src/julee --cov-fail-under=60 --cov-report=html:reports/htmlcov --cov-report=xml:reports/coverage.xml -m "not e2e and not integration"

# Tests that need something running, a Temporal server for instance. One
# test server per test, so the worker count is fixed rather than -n auto.
# There are none in julee itself since polling moved to julee-kits, and an
# empty selection (pytest exit code 5) is not a failure.
test-integration:
	@echo "Running integration tests..."
	@uv run pytest -m integration -n 2; status=$$?; \
	if [ $$status -eq 5 ]; then echo "No integration tests in this package."; exit 0; fi; \
	exit $$status

# Setup reports directory
reports:
	@mkdir -p reports

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
	uv run black src/julee/ viewpoints/src/
	uv run ruff check --fix src/julee/ viewpoints/src/

# Update uv.lock from pyproject.toml
update-requirements:
	@echo "Updating uv.lock from pyproject.toml..."
	uv lock --upgrade
	@echo "Lock file updated! Review changes before committing."

# Help target
help:
	@echo "Available targets:"
	@echo "  check           - The checks CI runs (lint, types, unit, integration, doctrine, kits)"
	@echo "  docs            - Build the documentation"
	@echo "  test-doctrine   - Doctrine tests against julee itself"
	@echo "  test-doctrine-kits - Doctrine tests against the kits in this workspace"
	@echo "  lint-python     - Python linting (black, ruff)"
	@echo "  test-python-unit - Python unit tests"
	@echo "  quality-fast-python - Fast Python quality checks (lint + unit tests)"
	@echo "  quality-full    - Full quality suite (types, security, all tests)"
	@echo "  quality-types   - Type checking with mypy"
	@echo "  quality-security- Security scanning with bandit"
	@echo "  test-unit       - Unit tests with coverage"
	@echo "  test-integration - Temporal pipeline tests (needs a test server)"
	@echo "  install         - Install project and dev dependencies via uv"
	@echo "  format-python   - Format Python code with black and ruff"
	@echo "  update-requirements - Upgrade uv.lock from pyproject.toml"
	@echo "  clean           - Clean up generated files"
	@echo "  reports         - Create reports directory"
	@echo "  help            - Show this help"
