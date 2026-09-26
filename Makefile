# Makefile for quality checks, testing and docs
# Requires uv: https://docs.astral.sh/uv/getting-started/installation/
.PHONY: install check docs release-notes release-prepare release-tag lint-python typecheck test-python-unit test-doctrine quality-fast-python quality-full quality-types quality-security test-unit reports clean help format-python update-requirements

# Install project and dev dependencies
install:
	uv sync --extra dev

# Python linting
lint-python:
	@echo "Linting Python code..."
	uv run ruff format --check src/julee/
	uv run ruff check src/julee/

# Type checking (fails on errors)
typecheck:
	@echo "Type checking..."
	uv run mypy src/julee/

# Python unit tests. Every test julee has needs nothing but Python, so
# there is nothing to leave out: no selector, and a test with no marker
# runs rather than hides. Doctrine has its own target below.
test-python-unit:
	@echo "Running Python unit tests..."
	uv run pytest --ignore=src/julee/core/doctrine

# Doctrine tests against julee itself
test-doctrine:
	@echo "Running doctrine tests..."
	uv run pytest src/julee/core/doctrine/

# The checks CI runs; run before pushing
check: lint-python typecheck test-python-unit test-doctrine

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

# Unit tests with coverage.
test-unit: reports
	@echo "Running unit tests with coverage..."
	uv run pytest --asyncio-mode=auto --cov=src/julee --cov-fail-under=60 --cov-report=html:reports/htmlcov --cov-report=xml:reports/coverage.xml

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
	uv run ruff format src/julee/
	uv run ruff check --fix src/julee/

# Update uv.lock from pyproject.toml
update-requirements:
	@echo "Updating uv.lock from pyproject.toml..."
	uv lock --upgrade
	@echo "Lock file updated! Review changes before committing."

# Help target
# Releasing
release-notes:
	uv run python -m julee.maintenance.release notes $(VERSION)

release-prepare:
	uv run python -m julee.maintenance.release prepare $(VERSION) \
		$(if $(NOTES),--message-file $(NOTES),--edit)

release-tag:
	uv run python -m julee.maintenance.release tag $(VERSION)

help:
	@echo "Available targets:"
	@echo "  check           - The checks CI runs (lint, types, unit, doctrine)"
	@echo "  docs            - Build the documentation"
	@echo "  test-doctrine   - Doctrine tests against julee itself"
	@echo "  lint-python     - Python linting (ruff)"
	@echo "  test-python-unit - Python unit tests"
	@echo "  quality-fast-python - Fast Python quality checks (lint + unit tests)"
	@echo "  quality-full    - Full quality suite (types, security, all tests)"
	@echo "  quality-types   - Type checking with mypy"
	@echo "  quality-security- Security scanning with bandit"
	@echo "  test-unit       - Unit tests with coverage"
	@echo "  install         - Install project and dev dependencies via uv"
	@echo "  format-python   - Format Python code with ruff"
	@echo "  update-requirements - Upgrade uv.lock from pyproject.toml"
	@echo "  clean           - Clean up generated files"
	@echo "  reports         - Create reports directory"
	@echo "  release-notes   - Draft release notes (VERSION=X.Y.Z, or omit to be asked)"
	@echo "  release-prepare - Release branch and PR (VERSION=X.Y.Z [NOTES=file])"
	@echo "  release-tag     - Tag after the release PR is merged (VERSION=X.Y.Z)"
	@echo "  help            - Show this help"
