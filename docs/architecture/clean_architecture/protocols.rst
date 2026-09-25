Protocols
=========

**Protocols define interfaces.**

Python Protocols are key to how Julee interfaces with infrastructure.

A :doc:`use case <use_cases>` depends on protocols and calls outward through
them. In hexagonal terms these are **driven ports**: the application drives
them, and an adapter in ``infrastructure/`` implements each one.
We use modern python typing to ensure infrastructure components
implement those interfaces, and this is relied upon by use cases
and leveraged by :doc:`dependency injection <dependency_injection>`.
This is why :doc:`applications </architecture/applications/index>` don't need to think about it,
they just run the use cases.

The Six Driven Ports
--------------------

Julee names six kinds of driven port.
Two questions tell them apart,
and :doc:`ADR 016 </ADRs/016-driven-ports>` is the decision behind them.

**What is it bound to?**
How many of its bounded context's :doc:`entities` does it name?

**Is it replay-safe?**
Must a :doc:`pipeline </architecture/solutions/pipelines>` reach it through a
Temporal activity, or may it call the port inline?

::

                              bound to
                  ┌──────────┬────────────┬──────────┐
                  │    0     │     1      │   2+     │
        ┌─────────┼──────────┼────────────┼──────────┤
        │ activity│  Oracle  │ Repository │ Service  │
        ├─────────┼──────────┴────────────┴──────────┤
        │         │  Calculator   deterministic      │
        │ inline  │  Witness      replay-stable      │
        │         │  Handler      native dispatch    │
        └─────────┴──────────────────────────────────┘

:doc:`Repositories <repositories>` store one entity each.
:doc:`Services <services>` transform between two or more.
:doc:`Oracles <oracles>` ask something the solution does not control.
All three do I/O, so a pipeline reaches them through an activity.

:doc:`Calculators <calculators>` work an answer out from what they were handed.
:doc:`Witnesses <witnesses>` report on the execution itself.
:doc:`Handlers <handlers>` hand work off to whatever comes next.
All three are safe to call inline, for three different reasons.

The name is where the second answer is recorded.
A reader can work out what a port is bound to by reading its signatures;
they cannot work out whether a workflow may call it inline.
``SchemaOracle`` says it must be reached through an activity.
``NewDataCalculator`` says a workflow may call it directly.

Finding Them
------------

Each kind lives in its own directory,
and doctrine finds a protocol by the directory it sits in
rather than by what it is called::

    domain/
    ├── models/          # entities
    ├── repositories/    # *Repository
    ├── services/        # *Service, and *Handler in *_handler.py
    ├── oracles/         # *Oracle
    ├── calculators/     # *Calculator
    └── witnesses/       # *Witness

Most bounded contexts use three of the six.

A protocol found in one of these directories
whose name claims none of the roles that directory offers
fails doctrine rather than being quietly ignored.
There are only two ways out: the name drifted and should be corrected,
or the protocol is in the wrong directory.

Repositories are the exception to the naming rule.
A repository declares itself by inheriting
:py:class:`~julee.repositories.base.RepositoryOf`,
which mypy reads as well as doctrine,
and that is a stronger claim than a suffix.

What They Deal In
-----------------

Repository, service and handler protocols are typed such that
they only deal in :doc:`entities` and simple primitives.

Oracles and witnesses are not, and this is the point of them.
An oracle returns whatever the remote system says, in that system's currency;
a witness returns what the runtime recorded.
Neither names an entity, because what they deal in was never ours to model.
