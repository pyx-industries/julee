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


Which declarations a family holds
---------------------------------

Most rules do not read your source directly. A parser first sorts
classes into families — entities, use cases, repository protocols and
the rest — by the directory a class sits in and, for use cases, by its
name. A rule that takes a family sees its members and nothing else, and
a class in no family is not shown to it. ``verify`` does not say which
classes those are. This does:

.. code-block:: bash

    julee doctrine census

It lists every class, function and call-valued assignment your source
declares at module level, with its file and line, and says which family
holds it or that none does. ``--target PATH`` works as it does for
``verify``, and ``--format json`` carries every declaration rather than
a summary. The JSON is provisional and will change.

**It reports family membership, not rule coverage.** Unclaimed means in
no family, not unchecked: the dependency rule reads a use case file's
imports whatever the file declares, and other rules import a layer's
modules and ask Python. Claimed means a member of a family, not
compliant. Most unclaimed classes are adapters and drivers, which have
no family and need none.

A declaration is in one of four states:

``claimed at its location``
    A family member carries its file and name.

``claimed by name``
    A family member carries only its name, and it is the one declaration
    of that name in the bounded context. A request or response a use
    case file imports is known to the parser this way.

``candidate``
    A family member carries only its name, and the bounded context
    declares that name more than once. None of the declarations is
    claimed, because nothing says which was meant; the name is listed as
    *ambiguous*. A name declared nowhere in the context is *external*.

``unclaimed``
    In no family. Those in a directory the parser fills a family from
    are listed first: the parser looked there and passed over them. A
    function beside an entity in ``domain/models/`` is the usual one,
    since no family holds a function.

What it reads is every ``.py`` file under ``search_root`` except test
files, anything under a directory whose name begins with a dot, and
anything git ignores, and it names what it left out. Source in a
directory that is not a bounded context is listed with the reason it is
not one. Nothing is imported.

It exits 0 when every file in scope was read, whatever it found:
whether an unclaimed class or an ambiguous name is a fault is a rule's
question, and the census is not a rule. It exits 1 when a file in scope
could not be read, or when the parser reports a class the census could
not find in the file named, because either way the report is not one to
rely on. It exits 2 when the target is not a julee solution.


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
