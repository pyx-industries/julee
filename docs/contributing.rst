Contributing
============

We welcome contributions to Julee! This guide will help you get started.

Development Setup
-----------------

1. Fork and clone the repository::

    git clone https://github.com/pyx-industries/julee.git
    cd julee

2. Create a virtual environment::

    python -m venv .venv
    source .venv/bin/activate

3. Install development dependencies::

    pip install -e ".[dev,docs]"

4. Install pre-commit hooks::

    pre-commit install


Code Style
----------

We use the following tools to maintain code quality:

**Ruff**
    Fast Python linter and formatter::

        ruff check .
        ruff format .

**Mypy**
    Static type checking::

        mypy src/julee apps

**Pre-commit**
    Automated checks before commit::

        pre-commit run --all-files


Testing
-------

Running Tests
~~~~~~~~~~~~~

Run the test suite::

    pytest

Run with coverage::

    pytest --cov

Run specific test files::

    pytest apps/api/tests/
    pytest src/julee/core/tests/entities/


Writing Tests
~~~~~~~~~~~~~

Place tests in ``tests/`` directories adjacent to the code:

- ``apps/{app}/tests/`` - Application tests
- ``apps/{app}/doctrine/`` - Application doctrine tests
- ``src/julee/{pkg}/tests/`` - Package unit tests
- ``src/julee/core/doctrine/`` - Core framework doctrine tests

Use pytest fixtures for common setup::

    @pytest.fixture
    def sample_document():
        return Document(
            id="test-doc",
            name="Test Document",
            content="Test content"
        )

    def test_document_creation(sample_document):
        assert sample_document.name == "Test Document"


Doctrine Verification
~~~~~~~~~~~~~~~~~~~~~

Julee uses doctrine tests to enforce architectural rules. The ``julee-admin``
CLI provides tools to inspect the codebase and verify compliance.

**Explore your solution**::

    julee-admin solution show          # See solution structure
    julee-admin contexts list          # List bounded contexts
    julee-admin entities list          # List domain entities

**View doctrine rules**::

    julee-admin doctrine list          # List doctrine areas
    julee-admin doctrine show          # Show all rules
    julee-admin doctrine show -v       # Verbose with definitions

**Verify compliance**::

    julee-admin doctrine verify        # Run doctrine tests
    julee-admin doctrine verify -v     # Verbose output

Run ``julee-admin --help`` to discover all available commands.


Architecture Guidelines
-----------------------


Domain Layer
~~~~~~~~~~~~

- Keep domain models pure and focused
- Use Pydantic for validation
- No infrastructure dependencies
- Protocol-based repository interfaces


Application Layer
~~~~~~~~~~~~~~~~~

- Use dependency injection
- Keep route handlers thin
- Delegate to use cases
- Clear request/response models


Infrastructure Layer
~~~~~~~~~~~~~~~~~~~~

- Implement repository protocols
- Handle external service interactions
- Proper error handling and retries
- Logging for debugging


Code Organization
-----------------

Follow the existing structure::

    julee/
    ├── apps/                  # Applications
    │   ├── admin/             # CLI tooling (julee-admin)
    │   ├── api/               # FastAPI application
    │   ├── sphinx/            # Sphinx documentation extensions
    │   ├── worker/            # Temporal worker
    │   └── {name}_mcp/        # MCP server applications
    ├── src/julee/             # Framework package
    │   ├── core/              # Core framework
    │   │   ├── doctrine/      # Doctrine tests (architecture rules)
    │   │   ├── entities/      # Domain entities
    │   │   ├── infrastructure/# Infrastructure implementations
    │   │   ├── repositories/  # Repository protocols
    │   │   ├── services/      # Service protocols
    │   │   └── use_cases/     # Business logic
    │   ├── contrib/           # Optional contributions
    │   ├── c4/                # C4 Model accelerator
    │   └── hcd/               # Human-Centered Design accelerator
    └── docs/                  # Documentation




Pull Requests
-------------

1. Create a feature branch::

    git checkout -b my-feature

2. Make your changes, don't forget tests

3. Ensure all tests pass::

    pytest
    ruff check .
    mypy src/julee apps

4. Commit with clear messages. Use the imperative mood, first line short.

5. Push and create PR::

    git push origin feature/my-feature


Documentation
-------------

Update documentation for:

- New features
- API changes
- Configuration options
- Architecture changes

Build docs locally::

    cd docs
    make html
    open _build/html/index.html

Or use autobuild for live reload::

    sphinx-autobuild docs docs/_build/html


Code Review
-----------

All PRs require review. Reviewers will check:

- Code quality and style
- Test coverage
- Documentation updates
- Architecture consistency
- Breaking changes

Be responsive to feedback and iterate on your PR.


License and IP
--------------

By contributing, you agree that your contributions will belong to Pyx Holdings Pty. Ltd.
who reserve all rights, including the right to distribute your contribution under the GPL.
