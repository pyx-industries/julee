Julee is a Framework
====================

**A reusable framework and a business application are different beasts.**
One is a vocabulary for building things; the other is the thing being built.

Julee is a framework for building resilient,
transparent, and accountable digital product supply chains.
It's a kind of orchestrator that manages :doc:`pipelines <solutions/pipelines>`,
using a set of idioms based on :doc:`Clean Architecture <clean_architecture/index>` principles.

A "digital product supply chain" is a way of thinking about how work gets done.
That work might involve humans, traditional automation, and AI agents or services.
At it's heart, Julee :doc:`applications <applications/index>` are processes that follow business rules.
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
Infrastructure can be swapped-out
(see :doc:`dependency injection <clean_architecture/dependency_injection>`),
business-logic and domain models can be adapted as requirements change over time,
and the system remains manageable even in the most complicated enterprises.
Essentially, the digital supply chain transparency creates an opportunity for good process governance;
risks can be identified and mitigated, strategies implemented, and processes refined over time.
Comprehensive test automation, clean and clear boundaries enable best practice.


Framework vs Solution
---------------------

**A framework provides vocabulary.** Julee's first-class concepts are
the building blocks for constructing digital supply chains:
:doc:`entities <clean_architecture/entities>` (domain models),
business processes (:doc:`use cases <clean_architecture/use_cases>`),
and :doc:`protocols <clean_architecture/protocols>`
(:doc:`repositories <clean_architecture/repositories>` and :doc:`services <clean_architecture/services>`).

**A :doc:`solution <solutions/index>` uses that vocabulary to say something specific.**
When you build a solution with Julee, your codebase should be organised
around your business domain—your bounded contexts—not around framework concepts.
A solution builds :doc:`accelerators <solutions/accelerators>`
from :doc:`pipelines <solutions/pipelines>`,
exposed through :doc:`API <applications/api>`, :doc:`CLI <applications/cli>`,
:doc:`Worker <applications/worker>`, or :doc:`UI <applications/ui>` entry points.

If you're familiar with Django, Julee is a framework in the same way.
For everyone else, it's a toolkit for building software systems
that meet certain types of business need.


Runtime Dependencies
--------------------

.. uml:: diagrams/c4_context.puml

A :doc:`deployed <deployment>` Julee application depends on:

- **Infrastructure** you deploy (Temporal, Object Storage, PostgreSQL)
- **Services** from the supply chain (third-party APIs, self-hosted services, bundled services)
