Contributing
============

We welcome contributions to Julee! This guide will help you get started.

Development Setup
-----------------

Julee is built with `uv <https://docs.astral.sh/uv/>`_, which manages the
virtual environment for you.

1. Fork and clone the repository::

    git clone https://github.com/yourusername/julee.git
    cd julee

2. Install the project and its development dependencies::

    make install

   That runs ``uv sync --extra dev``, creating ``.venv`` if it is not
   already there. Run commands through ``uv run``, or activate the
   environment with ``source .venv/bin/activate`` if you prefer.

.. note::

    ``make install-hooks`` used to install a post-commit hook that ran the
    full quality suite in the background after every commit. It has been
    retired: the runs piled up, in worktrees as well, and CI now runs
    ``make check`` on every pull request. Removing the make target does not
    remove a hook that is already installed, so if you ever ran it, delete
    the hook::

        rm .git/hooks/post-commit


Code Style
----------

We use the following tools to maintain code quality:

**Black**
    The formatter. Ruff is configured for linting only, so do not run
    ``ruff format`` — it disagrees with black and will reformat files the
    change never touched::

        uv run black src/julee/

**Ruff**
    The linter::

        uv run ruff check src/julee/

**Mypy**
    Static type checking, in strict mode::

        uv run mypy src/julee/

``make format-python`` runs the formatter over the tree, and
``make lint-python`` checks formatting and linting without changing
anything.


Testing
-------

Running Tests
~~~~~~~~~~~~~

Run the test suite::

    uv run pytest

Coverage is already in ``addopts``, so every run reports it.

Run a specific test file::

    uv run pytest src/julee/core/tests/doctrine_rules/test_port.py

The doctrine tests are excluded from the unit run and have a target of
their own, because they check a codebase rather than the framework's
behaviour::

    make test-doctrine

To run doctrine against a codebase other than julee, point
``JULEE_TARGET`` at it::

    JULEE_TARGET=/path/to/solution uv run pytest src/julee/core/doctrine/


Writing Tests
~~~~~~~~~~~~~

Place tests in ``tests/`` directories adjacent to the code they test, for
example ``src/julee/repositories/tests/`` and
``src/julee/core/usecases/tests/``.

Mark anything that is not a plain Python unit test, so that it is left out
of the fast run: ``integration``, ``e2e``, ``llm``, ``contract`` and
``slow`` are declared in ``pyproject.toml``. An unmarked test runs, which
is deliberate — a test hides by being marked, never by being forgotten.

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


Architecture Guidelines
-----------------------


The architecture is not advice here: doctrine enforces it, and the
doctrine tests are the rules (see :doc:`/ADRs/002-doctrine-test-architecture`).
A change that breaks the layout fails ``make check`` rather than review.

Domain Layer
~~~~~~~~~~~~

- Keep domain models pure and focused
- Use Pydantic for validation
- No infrastructure dependencies
- Protocol-based ports, one per file


Application Layer
~~~~~~~~~~~~~~~~~

- Use dependency injection
- Keep route functions thin
- Delegate to use cases
- Clear request/response models


Infrastructure Layer
~~~~~~~~~~~~~~~~~~~~

- Implement the domain's port protocols
- Handle external service interactions
- Proper error handling and retries
- Logging for debugging


Driven Ports
~~~~~~~~~~~~

A use case depends on protocols and calls outward through them.
:doc:`/ADRs/016-driven-ports` names six, and which one you are writing
decides both the directory it goes in and what it may be called:

.. list-table::
   :header-rows: 1
   :widths: 16 18 22 44

   * - Port
     - Bound to
     - Called in a workflow
     - Lives in
   * - Repository
     - one entity
     - through an activity
     - ``domain/repositories/``, as ``{Entity}Repository``
   * - Service
     - two or more entities
     - through an activity
     - ``domain/services/``, as ``{Capability}Service``
   * - Oracle
     - no entity
     - through an activity
     - ``domain/oracles/``, as ``{Capability}Oracle``
   * - Calculator
     - any number
     - inline
     - ``domain/calculators/``, as ``{Capability}Calculator``
   * - Witness
     - no entity
     - inline
     - ``domain/witnesses/``, as ``{Subject}Witness``
   * - Handler
     - any, returns ``Acknowledgement``
     - inline
     - ``domain/services/``, in ``*_handler.py``

A repository declares its entity by inheriting ``RepositoryOf[Entity]``,
which is why it is the one port with no naming rule. The other five are
found by their directory and held to their name, so a protocol whose name
claims nothing fails doctrine rather than being quietly ignored.


Code Organization
-----------------

Two layouts matter, and they are not the same thing. This repository holds
the framework; the layout doctrine enforces is the one a *bounded context*
follows, wherever it lives.

The framework repository
~~~~~~~~~~~~~~~~~~~~~~~~

:doc:`/ADRs/012-framework-and-kits` puts julee's code in three rings. The
test for placing something is whether a solution in an unrelated domain
would want it::

    julee/
    ├── src/julee/
    │   ├── core/          # Kernel: the concepts every solution uses
    │   │   └── doctrine/  #   the rules, and the rule functions they call
    │   ├── integrations/  # Batteries, each behind a pip extra
    │   │   ├── fastapi/
    │   │   ├── minio/
    │   │   └── temporal/
    │   └── repositories/  # Repository bases: memory, file
    └── docs/
        └── ADRs/          # Architecture decision records

Code naming a specific business entity — a document, a credential, a
persona — is not kernel code. It belongs in a kit, in the separate
``julee-kits`` repository, and ships as its own distribution.

A bounded context
~~~~~~~~~~~~~~~~~

This is the layout doctrine reads, in a kit or in a solution of your own::

    <bounded_context>/
    ├── domain/
    │   ├── models/        # Entities
    │   ├── repositories/  # Repository protocols
    │   ├── services/      # Service protocols, and *_handler.py
    │   ├── oracles/       # Oracle protocols
    │   ├── calculators/   # Calculator protocols
    │   └── witnesses/     # Witness protocols
    ├── usecases/          # Application business rules
    ├── infrastructure/    # Implementations of the protocols above
    │   ├── handlers/
    │   └── repositories/
    │       ├── memory/
    │       ├── minio/
    │       └── temporal/
    ├── apps/              # Composition roots: api, worker, cli
    └── tests/

Every one of these directories is found by name, so a context that spells
one differently has code doctrine cannot see. That is not a passing grade:
a package holding modules doctrine reads nothing out of fails a canary
rule rather than going quiet.

A context may hold other packages besides these — ``julee-hcd`` has
``parsers/``, ``serializers/`` and ``templates/``. Doctrine does not mind;
it checks the directories it knows about.

The port directories are per :doc:`/ADRs/016-driven-ports` and only some
contexts need them: most have ``models/``, ``repositories/`` and
``usecases/`` and nothing else under ``domain/``. Create a directory when
you have something to put in it.




Pull Requests
-------------

Never commit to ``master``. Every change goes through a branch and a pull
request.

1. Create a feature branch. Use a plain descriptive name — no ``feat/``
   or ``fix/`` prefixes::

    git checkout -b my-feature

2. Make your changes, don't forget tests

3. Run the full check. This is what CI runs, so run all of it rather than
   the part you think your change touched::

    make check

   If you changed a docstring, a public signature, a module-level type
   alias or anything under ``docs/``, build the documentation too. It runs
   with ``-W`` and ``nitpicky = True``, so an unresolved cross-reference
   fails::

    make docs

4. Commit with clear messages. Use the imperative mood, first line short.

5. Push and open a pull request::

    git push -u origin my-feature


Documentation
-------------

Update documentation for:

- New features
- API changes
- Configuration options
- Architecture changes

Build docs locally from the repository root::

    make docs
    open docs/_build/html/index.html

Use ``make docs`` rather than ``make html`` inside ``docs/``: the root
target passes ``-W``, so warnings fail the build the way CI does, and the
one inside ``docs/`` does not. A local build that looks green while CI
rejects it is worse than no local build.

Or use autobuild for live reload, which does not enforce warnings::

    uv run --extra docs sphinx-autobuild docs docs/_build/html

Architectural decisions go in ``docs/ADRs/`` and are published with the
rest of the documentation. Add new ones to the index table and to the
toctree in ``docs/ADRs/index.md``.


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
