Julee is a Framework
====================

**A reusable framework and a business application are different beasts.**
One is a vocabulary for building things; the other is the thing being built.

Julee is a framework for building resilient,
transparent, and accountable digital product supply chains.
It's a kind of orchestrator that manages work pipelines,
using a set of idioms based on "Clean Architecture" principles.

A "digital product supply chain" is a way of thinking about how work gets done.
That work might involve humans, traditional automation, and AI agents or services.
At it's heart, Julee applications are processes that follow business rules.
They are done in a way that leaves an impeccable audit trail,
which can be used to create a "digital product passport"
to accompany the output of the process.
This makes Julee particularly suitable for processes
with non-trivial compliance requirements, such as responsible AI requirements
or algorithmic due-diligence of high-integrity supply chain information.

The processes that Julee orchestrates may depend on unreliable services,
e.g. services which might temporarily fail, be rate-limited, or timeout, etc.
Julee runs the work pipelines in a way that is resilient,
with intelligent retries and so on.
It makes tradeoffs in favour of reliability and resilience,
at the expense of throughput and latency.
Julee is most suitable for processes which must be done correctly,
and which may be complex and long-running.

The clean architecture principles allow Julee applications to evolve.
Infrastructure can be swapped-out (without needing to rewire everything),
business-logic and domain models can be adapted as requirements change over time,
and the system remains manageable even in the most complicated enterprises.
Essentially, the digital supply chain transparency creates an opportunity for good process governance;
risks can be identified and mitigated, strategies implemented, and processes refined over time.
Comprehensive test automation, clean and clear boundaries enable best practice.


Framework vs Solution
---------------------

**A framework provides vocabulary.** Julee's first-class concepts are
the building blocks for constructing digital supply chains:
entities (domain models), business processes (use cases),
and protocols (repositories and services).

**A solution uses that vocabulary to say something specific.**
When you build a solution with Julee, your codebase should be organised
around your business domain—your bounded contexts—not around framework concepts.

If you're familiar with Django, Julee is a framework in the same way.
For everyone else, it's a toolkit for building software systems
that meet certain types of business need.

See :doc:`solutions/index` for how to structure a Julee solution.


Runtime Dependencies
--------------------

.. uml:: diagrams/c4_context.puml

A deployed Julee application depends on:

- **Infrastructure** you deploy (Temporal, Object Storage, PostgreSQL)
- **Services** from the supply chain (third-party APIs, self-hosted services, bundled services)


Build-time Composition
----------------------

.. uml:: diagrams/c4_component.puml

At build time, your application composes components from the framework:

- **Julee Framework** provides contrib modules: domain protocols, use case implementations, Temporal workflows, repository and service implementations
- **Your Application** extends the framework: your domain models, use cases, configuration, API and workers

This is a compile-time dependency—you ``pip install julee`` and import its components.
