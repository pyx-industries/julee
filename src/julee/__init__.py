"""Julee - Clean architecture for accountable and transparent digital supply chains.

A reusable framework and a business application are different beasts. One is a
vocabulary for building things; the other is the thing being built.

Julee is a framework for building resilient, transparent, and accountable
digital product supply chains. It's an orchestrator that manages pipelines,
using idioms based on Clean Architecture principles.

What is a Digital Product Supply Chain?
---------------------------------------
A "digital product supply chain" is a way of thinking about how work gets done.
That work might involve humans, traditional automation, and AI agents or services.

At its heart, Julee applications are processes that follow business rules. They
execute in a way that leaves an impeccable audit trail, which can be used to
create a "digital product passport" to accompany the output of the process.

This makes Julee particularly suitable for processes with non-trivial compliance
requirements, such as responsible AI requirements or algorithmic due-diligence
of high-integrity supply chain information.

Resilience Over Speed
---------------------
The processes that Julee orchestrates may depend on unreliable services - services
which might temporarily fail, be rate-limited, or timeout. Julee runs work pipelines
in a way that is resilient, with intelligent retries and backoff.

It makes tradeoffs in favour of reliability and resilience, at the expense of
throughput and latency. Julee is most suitable for processes which must be done
correctly, and which may be complex and long-running.

Evolvability
------------
Clean Architecture principles allow Julee applications to evolve. Infrastructure
can be swapped-out via dependency injection, business-logic and domain models can
be adapted as requirements change over time, and the system remains manageable
even in the most complicated enterprises.

The digital supply chain transparency creates an opportunity for good process
governance: risks can be identified and mitigated, strategies implemented, and
processes refined over time. Comprehensive test automation and clean boundaries
enable best practice.

Framework vs Solution
---------------------
**A framework provides vocabulary.** Julee's first-class concepts are the building
blocks for constructing digital supply chains:

- **Entities** - Domain models (see :py:mod:`julee.core.entities.entity`)
- **Use Cases** - Business processes (see :py:mod:`julee.core.entities.use_case`)
- **Repositories** - Persistence protocols (see :py:mod:`julee.core.entities.repository_protocol`)
- **Services** - Transformation protocols (see :py:mod:`julee.core.entities.service_protocol`)

**A solution uses that vocabulary to say something specific.** When you build a
solution with Julee, your codebase should be organised around your business
domain - your bounded contexts - not around framework concepts.

If you're familiar with Django, Julee is a framework in the same way. For everyone
else, it's a toolkit for building software systems that meet certain types of
business need.

Runtime Dependencies
--------------------
A deployed Julee application depends on:

- **Infrastructure** you deploy (Temporal, Object Storage, PostgreSQL)
- **Services** from the supply chain (third-party APIs, self-hosted services)
"""

__version__ = "0.1.5"
