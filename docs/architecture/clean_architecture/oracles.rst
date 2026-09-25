Oracles
=======

**Oracles ask something you don't control.**

An oracle calls out to a remote endpoint, a filesystem, a signing service,
a liveness probe—something outside the solution—and gets an answer back
in that thing's own currency rather than yours.

::

    class SchemaOracle(Protocol):
        async def fetch(self, url: str) -> dict[str, Any]: ...

An oracle names no :doc:`entity <entities>`.
That is not an oversight, and it is what distinguishes an oracle
from a :doc:`repository <repositories>` or a :doc:`service <services>`.
Nothing it deals in has been modelled,
because modelling foreign JSON as a domain entity
would be a claim the solution cannot keep.
If the remote system changes its response shape tomorrow,
a ``dict`` is still honest and an entity would have been a lie.

Oracles are defined as :doc:`protocols`;
the :doc:`DI container <dependency_injection>` provides implementations.
Those implementations live in ``infrastructure/``,
because an oracle is where a bounded context
admits a runtime dependency on something outside the solution.

Oracles Must Be Activities
--------------------------

An oracle performs I/O, so its answer can differ between replays.
A :doc:`pipeline </architecture/solutions/pipelines>` reaches it through a
Temporal activity, never inline—the same treatment
:doc:`repositories` and :doc:`services` get, and for the same reason.

If You Wanted An Entity
-----------------------

Sometimes the honest answer is that the foreign data
*should* be modelled, and you have simply not done it yet.
Model it, return the entity, and what you have is a repository
bound to that entity—not an oracle at all.

The test is whether you can keep the promise.
An oracle says "here is what they told me".
A repository says "here is one of ours".

Recognising One
---------------

These were all written before the word existed,
and each author reached for whichever of ``*Repository``
or ``*Service`` felt least wrong:

- ``fetch(url: str) -> dict[str, Any]`` — fetching a JSON schema over HTTP
- ``check_health() -> dict[str, list[str]]`` — an operational probe
- ``get_prompt(name: str) -> str`` — reading a template off disk
- ``sign_credential(...) -> dict[str, Any]`` — calling a signing service

Four authors in four codebases split evenly between two words
that both fit badly. That is what a missing name looks like.
