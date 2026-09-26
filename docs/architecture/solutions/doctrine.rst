Checking a Solution
===================

**Doctrine is not advice.** It is a suite of tests that reads your
codebase and objects to what does not hold. julee runs it against itself
and against every kit; this page is how you run it against yours.

Two ways, same rules, same result. Pick whichever fits where you want
the answer to appear.

.. code-block:: bash

    uv add 'julee[doctrine]'


As a command
------------

.. code-block:: bash

    julee doctrine verify

It checks the directory you are standing in, or the nearest julee
solution above it, and exits non-zero on a violation — so it drops into
CI without ceremony:

.. code-block:: yaml

    - run: uv sync --extra doctrine
    - run: uv run julee doctrine verify

``--target PATH`` checks somewhere else, which is what a monorepo wants:

.. code-block:: bash

    julee doctrine verify --target packages/billing


In your own test run
--------------------

.. code-block:: bash

    pytest --julee-doctrine

Doctrine's objections then appear among your own failures, at the moment
you made them, rather than in a separate run somebody has to remember.
Installing julee is enough — the plugin registers itself and your
``conftest.py`` needs nothing.

To have it always on:

.. code-block:: toml

    [tool.pytest.ini_options]
    addopts = "--julee-doctrine"


What you have to declare
------------------------

One section, and doctrine knows where to look:

.. code-block:: toml

    [tool.julee]
    search_root = "src"        # where your bounded contexts live
    kits = ["hcd", "c4"]       # any kits you have adopted

Without ``[tool.julee]`` both entry points stop and say so. They do not
fall back to checking nothing, because a run over nothing passes every
rule and reads exactly like a run over a codebase that complies — the
mistake that :doc:`ADR 002 </ADRs/002-doctrine-test-architecture>` calls
a rule that finds nothing, and the one julee made about *itself* for
several releases.

For the same reason, a codebase that genuinely has no bounded contexts
says so rather than passing quietly:

.. code-block:: toml

    [tool.julee]
    search_root = "src/acme_docs"
    bounded_contexts = "none"   # a projection over kits; no domain of its own


What you will see first
-----------------------

A solution adopting doctrine mid-life sees every violation at once, and
there is deliberately no way to silence them one by one yet. A list of
accepted violations is a list that goes stale silently, which is the
failure doctrine exists to catch; the escape hatch will be designed
around what actually blocks a real migration rather than guessed at now.

So read the first run as a survey. The rules that will fire hardest are
:doc:`entity immutability </architecture/clean_architecture/entities>`
and the :doc:`driven port
</ADRs/016-driven-ports>` names, because both are conventions most
codebases have never been asked to keep.


One thing to know about semantic claims
---------------------------------------

If your solution or a kit publishes a ``semantics.toml``, the claims in
it name classes by dotted path. The near end of a claim — the class the
publishing package owns — is resolved by **reading the source** in the
directory being checked, so the answer is about that directory and not
about what happens to be installed where doctrine runs.

That means you can check a codebase you have not installed:

.. code-block:: bash

    julee doctrine verify --target ../some-kit

The far end may name a kit that nothing here has installed, which is how
a claim stays useful to a solution that later adopts both. So a far end
is resolved by import, and only asked about at all when its package is
present. What can be checked, is.
